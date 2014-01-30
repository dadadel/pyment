#!/usr/bin/python

import unittest
import pyment.docstring as docs

myelem = '    def my_method(self, first, second=None, third="value"):'
mydocs = '''        """This is a description of a method.
        It is on several lines.
        Several styles exists:
            -javadoc,
            -reST,
            -cstyle.
        It uses the javadoc style.

        @param first: the 1st argument.
        with multiple lines
        @type first: str
        @param second: the 2nd argument.
        @return: the result value
        @rtype: int
        @raise: KeyError

        """'''
mygrpdocs = '''
    """
    My desc of groups style.
    On two lines.

    Parameters:
      first: the 1st param
      second: the 2nd param
      third: the 3rd param

    Returns:
      a value in a string

    Raises:
      KeyError: when a key error
      OtherError: when an other error
    """'''


class DocStringTests(unittest.TestCase):

    def testAutoInputStyleJavadoc(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        self.failUnless(d.get_input_style() == 'javadoc')

    def testAutoInputStyleReST(self):
        doc = mydocs.replace("@", ":")
        d = docs.DocString(myelem, '    ', doc)
        self.failUnless(d.get_input_style() == 'reST')

    def testAutoInputStyleGroups(self):
        doc = mygrpdocs
        d = docs.DocString(myelem, '    ', doc)
        self.failUnless(d.get_input_style() == 'groups')

    def testParsingElement(self):
        d = docs.DocString(myelem, '    ')
        self.failUnless(d.element['type'] == 'def')
        self.failUnless(d.element['name'] == 'my_method')
        self.failUnless(len(d.element['params']) == 3)
        self.failUnless(type(d.element['params'][0]) is str)
        self.failUnless(d.element['params'][2] == ('third', '"value"'))

    def testIfParsedDocs(self):
        doc = mydocs
        # nothing to parse
        d = docs.DocString(myelem, '    ')
        d.parse_docs()
        self.failIf(d.parsed_docs)
        # parse docstring given at init
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.failUnless(d.parsed_docs)
        # parse docstring given in parsing method
        d = docs.DocString(myelem, '    ')
        d.parse_docs(doc)
        self.failUnless(d.parsed_docs)

    def testParsingDocsDesc(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.failUnless(d.docs['in']['desc'].strip().startswith('This '))
        self.failUnless(d.docs['in']['desc'].strip().endswith('style.'))

    def testParsingGroupsDocsDesc(self):
        doc = mygrpdocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.failUnless(d.docs['in']['desc'].strip().startswith('My '))
        self.failUnless(d.docs['in']['desc'].strip().endswith('lines.'))

    def testParsingDocsParams(self):
        doc = mydocs.replace("@", ":")
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.failUnless(len(d.docs['in']['params']) == 2)
        self.failUnless(type(d.docs['in']['params'][1]) is tuple)
        # param's name
        self.failUnless(d.docs['in']['params'][1][0] == 'second')
        # param's type
        self.failUnless(d.docs['in']['params'][0][2] == 'str')
        self.failIf(d.docs['in']['params'][1][2])
        # param's description
        self.failUnless(d.docs['in']['params'][0][1].startswith("the 1"))

    def testParsingGroupsDocsParams(self):
        doc = mygrpdocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.failUnless(len(d.docs['in']['params']) == 3)
        self.failUnless(d.docs['in']['params'][0][0] == 'first')
        self.failUnless(d.docs['in']['params'][0][1].startswith('the 1'))
        self.failUnless(d.docs['in']['params'][2][1].startswith('the 3rd'))

    def testParsingDocsReturn(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.failUnless(d.docs['in']['return'].startswith('the result'))
        self.failUnless(d.docs['in']['rtype'] == 'int')

    def testParsingGroupsDocsReturn(self):
        doc = mygrpdocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.failUnless(d.docs['in']['return'] == 'a value in a string')

    def testGeneratingDocsDesc(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        d.generate_docs()
        self.failUnless(d.docs['out']['desc'] == d.docs['in']['desc'])

    def testGeneratingDocsReturn(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        d.generate_docs()
        self.failUnless(d.docs['in']['return'].startswith('the result'))
        self.failUnless(d.docs['in']['rtype'] == 'int')

    def testGeneratingDocsRaise(self):
        self.fail("TODO!")

    def testGeneratingDocsParams(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        d.generate_docs()
        self.failUnless(len(d.docs['out']['params']) == 3)
        self.failUnless(type(d.docs['out']['params'][2]) is tuple)
        self.failUnless(d.docs['out']['params'][2] == ('third', '', None, '"value"'))
        # param's description
        self.failUnless(d.docs['out']['params'][1][1].startswith("the 2"))

    def testNoParam(self):
        elem = "    def noparam():"
        doc = """        '''the no param docstring
        '''"""
        d = docs.DocString(elem, '    ', doc, input_style='javadoc')
        d.parse_docs()
        d.generate_docs()
        self.failIf(d.docs['out']['params'])

    def testOneLineDocs(self):
        elem = "    def oneline(self):"
        doc = """        '''the one line docstring
        '''"""
        d = docs.DocString(elem, '    ', doc, input_style='javadoc')
        d.parse_docs()
        d.generate_docs()
        #print(d.docs['out']['raw'])
        self.failIf(d.docs['out']['raw'].count('\n'))


def main():
    unittest.main()

if __name__ == '__main__':
    main()

