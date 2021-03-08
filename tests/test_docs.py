#!/usr/bin/python
# -*- coding: utf-8 -*-
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
        @raise KeyError: raises a key error exception
        @raise OtherError: raises an other error exception

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

googledocs = '''"""This is a Google style docs.

    Args:
      first(str): this is the first param
      second: this is a second param
      third(str, optional): this is a third param

    Returns:
      This is a description of what is returned

    Raises:
      KeyError: raises an exception
      OtherError: when an other error
"""'''

mygrpdocs2 = '''
    """
    My desc of an other kind 
    of groups style.

    Params:
      first -- the 1st param
      second -- the 2nd param
      third -- the 3rd param

    Returns:
      a value in a string

    Raises:
      KeyError -- when a key error
      OtherError -- when an other error
    """'''

mynumpydocs = '''
    """
    My numpydoc description of a kind 
    of very exhautive numpydoc format docstring.

    Parameters
    ----------
    first : array_like
        the 1st param name `first`
    second :
        the 2nd param
    third : {'value', 'other'}, optional
        the 3rd param, by default 'value'

    Returns
    -------
    string
        a value in a string

    Raises
    ------
    KeyError
        when a key error
    OtherError
        when an other error

    See Also
    --------
    a_func : linked (optional), with things to say
             on several lines
    some blabla

    Note
    ----
    Some informations.

    Some maths also:
    .. math:: f(x) = e^{- x}

    References
    ----------
    Biblio with cited ref [1]_. The ref can be cited in Note section.

    .. [1] Adel Daouzli, Sylvain Saïghi, Michelle Rudolph, Alain Destexhe, 
       Sylvie Renaud: Convergence in an Adaptive Neural Network: 
       The Influence of Noise Inputs Correlation. IWANN (1) 2009: 140-148

    Examples
    --------
    This is example of use
    >>> print "a"
    a

    """'''


def torest(docs):
    docs = docs.replace("@", ":")
    docs = docs.replace(":return", ":returns")
    docs = docs.replace(":raise", ":raises")
    return docs


class DocStringTests(unittest.TestCase):

    def testChekListParamsGoogledoc(self):
        doc = googledocs
        d = docs.DocString(myelem, '    ', doc)
        d._extract_docs_params()
        self.assertTrue(d.get_input_style() == 'google')

    def testAutoInputStyleGoogledoc(self):
        doc = googledocs
        d = docs.DocString(myelem, '    ', doc)
        self.assertTrue(d.get_input_style() == 'google')

    def testAutoInputStyleNumpydoc(self):
        doc = mynumpydocs
        d = docs.DocString(myelem, '    ', doc)
        self.assertTrue(d.get_input_style() == 'numpydoc')

    def testAutoInputStyleJavadoc(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        self.assertTrue(d.get_input_style() == 'javadoc')

    def testAutoInputStyleReST(self):
        doc = torest(mydocs)
        d = docs.DocString(myelem, '    ', doc)
        self.assertTrue(d.get_input_style() == 'reST')

    def testAutoInputStyleGroups(self):
        doc = mygrpdocs
        d = docs.DocString(myelem, '    ', doc)
        self.assertTrue(d.get_input_style() == 'groups')

    def testSameOutputJavadocReST(self):
        doc = mydocs
        dj = docs.DocString(myelem, '    ')
        dj.parse_docs(doc)
        doc = torest(mydocs)
        dr = docs.DocString(myelem, '    ')
        dr.parse_docs(doc)
        self.assertEqual(dj.get_raw_docs(), dr.get_raw_docs())

    def testParsingElement(self):
        d = docs.DocString(myelem, '    ')
        self.assertTrue(d.element['deftype'] == 'def')
        self.assertTrue(d.element['name'] == 'my_method')
        self.assertTrue(len(d.element['params']) == 3)
        self.assertTrue(type(d.element['params'][0]['param']) is str)
        self.assertTrue((d.element['params'][2]['param'], d.element['params'][2]['default']) == ('third', '"value"'))

    def testIfParsedDocs(self):
        doc = mydocs
        # nothing to parse
        d = docs.DocString(myelem, '    ')
        d.parse_docs()
        self.assertFalse(d.parsed_docs)
        # parse docstring given at init
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(d.parsed_docs)
        # parse docstring given in parsing method
        d = docs.DocString(myelem, '    ')
        d.parse_docs(doc)
        self.assertTrue(d.parsed_docs)

    def testParsingDocsDesc(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(d.docs['in']['desc'].strip().startswith('This '))
        self.assertTrue(d.docs['in']['desc'].strip().endswith('style.'))

    def testParsingGroupsDocsDesc(self):
        doc = mygrpdocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(d.docs['in']['desc'].strip().startswith('My '))
        self.assertTrue(d.docs['in']['desc'].strip().endswith('lines.'))
    
    def testParsingNumpyDocsDesc(self):
        doc = mynumpydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(d.docs['in']['desc'].strip().startswith('My numpydoc'))
        self.assertTrue(d.docs['in']['desc'].strip().endswith('format docstring.'))

    def testParsingGoogleDocsDesc(self):
        doc = googledocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(d.docs['in']['desc'].strip().startswith('This is a Google style docs.'))

    def testParsingDocsParams(self):
        doc = torest(mydocs)
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(len(d.docs['in']['params']) == 2)
        self.assertTrue(type(d.docs['in']['params'][1]) is tuple)
        # param's name
        self.assertTrue(d.docs['in']['params'][1][0] == 'second')
        # param's type
        self.assertTrue(d.docs['in']['params'][0][2] == 'str')
        self.assertFalse(d.docs['in']['params'][1][2])
        # param's description
        self.assertTrue(d.docs['in']['params'][0][1].startswith("the 1"))

    def testParsingGoogleDocsParams(self):
        doc = googledocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(len(d.docs['in']['params']) == 3)
        self.assertTrue(d.docs['in']['params'][0][0] == 'first')
        self.assertTrue(d.docs['in']['params'][0][2] == 'str')
        self.assertTrue(d.docs['in']['params'][0][1].startswith('this is the first'))
        self.assertFalse(d.docs['in']['params'][1][2])
        self.assertTrue(d.docs['in']['params'][2][1].startswith('this is a third'))
        self.assertTrue(d.docs['in']['params'][2][2] == 'str')

    def testParsingGroupsDocsParams(self):
        doc = mygrpdocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(len(d.docs['in']['params']) == 3)
        self.assertTrue(d.docs['in']['params'][0][0] == 'first')
        self.assertTrue(d.docs['in']['params'][0][1].startswith('the 1'))
        self.assertTrue(d.docs['in']['params'][2][1].startswith('the 3rd'))

    def testParsingGroups2DocsParams(self):
        doc = mygrpdocs2
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(len(d.docs['in']['params']) == 3)
        self.assertTrue(d.docs['in']['params'][0][0] == 'first')
        self.assertTrue(d.docs['in']['params'][0][1].startswith('the 1'))
        self.assertTrue(d.docs['in']['params'][2][1].startswith('the 3rd'))

    def testParsingNumpyDocsParams(self):
        doc = mynumpydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(len(d.docs['in']['params']) == 3)
        self.assertTrue(d.docs['in']['params'][0][0] == 'first')
        self.assertTrue(d.docs['in']['params'][0][2] == 'array_like')
        self.assertTrue(d.docs['in']['params'][0][1].strip().startswith('the 1'))
        self.assertFalse(d.docs['in']['params'][1][2])
        self.assertTrue(d.docs['in']['params'][2][1].strip().endswith("default 'value'"))

    def testParsingDocsRaises(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        d.generate_docs()
        self.assertTrue(len(d.docs['in']['raises']) == 2)
        self.assertTrue(d.docs['in']['raises'][0][0].startswith('KeyError'))
        self.assertTrue(d.docs['in']['raises'][0][1].startswith('raises a key'))
        self.assertTrue(d.docs['in']['raises'][1][0].startswith('OtherError'))
        self.assertTrue(d.docs['in']['raises'][1][1].startswith('raises an other'))

    def testParsingGoogleDocsRaises(self):
        doc = googledocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(len(d.docs['in']['raises']) == 2)
        self.assertTrue(d.docs['in']['raises'][0][0] == 'KeyError')
        self.assertTrue(d.docs['in']['raises'][0][1].startswith('raises an'))
        self.assertTrue(d.docs['in']['raises'][1][0] == 'OtherError')
        self.assertTrue(d.docs['in']['raises'][1][1].startswith('when an other'))

    def testParsingGroupsDocsRaises(self):
        doc = mygrpdocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(len(d.docs['in']['raises']) == 2)
        self.assertTrue(d.docs['in']['raises'][0][0] == 'KeyError')
        self.assertTrue(d.docs['in']['raises'][0][1].startswith('when a key'))
        self.assertTrue(d.docs['in']['raises'][1][0] == 'OtherError')
        self.assertTrue(d.docs['in']['raises'][1][1].startswith('when an other'))

    def testParsingGroups2DocsRaises(self):
        doc = mygrpdocs2
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(len(d.docs['in']['raises']) == 2)
        self.assertTrue(d.docs['in']['raises'][0][0] == 'KeyError')
        self.assertTrue(d.docs['in']['raises'][0][1].startswith('when a key'))
        self.assertTrue(d.docs['in']['raises'][1][0] == 'OtherError')
        self.assertTrue(d.docs['in']['raises'][1][1].startswith('when an other'))

    def testParsingNumpyDocsRaises(self):
        doc = mynumpydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(len(d.docs['in']['raises']) == 2)
        self.assertTrue(d.docs['in']['raises'][0][0] == 'KeyError')
        self.assertTrue(d.docs['in']['raises'][0][1].strip().startswith('when a key'))
        self.assertTrue(d.docs['in']['raises'][1][0] == 'OtherError')
        self.assertTrue(d.docs['in']['raises'][1][1].strip().startswith('when an other'))

    def testParsingDocsReturn(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(d.docs['in']['return'].startswith('the result'))
        self.assertTrue(d.docs['in']['rtype'] == 'int')

    def testParsingGroupsDocsReturn(self):
        doc = mygrpdocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(d.docs['in']['return'] == 'a value in a string')

    def testParsingGoogleDocsReturn(self):
        doc = googledocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(d.docs['in']['return'][0][1] == 'This is a description of what is returned')

    def testParsingNumpyDocsReturn(self):
        doc = mynumpydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(d.docs['in']['return'][0][1] == 'a value in a string')
        d.set_output_style('numpydoc')

    def testGeneratingDocsDesc(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        d.generate_docs()
        self.assertTrue(d.docs['out']['desc'] == d.docs['in']['desc'])

    def testGeneratingDocsReturn(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        d.generate_docs()
        self.assertTrue(d.docs['out']['return'].startswith('the result'))
        self.assertTrue(d.docs['out']['rtype'] == 'int')

    def testGeneratingDocsRaise(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        d.generate_docs()
        self.assertTrue(len(d.docs['out']['raises']) == 2)
        self.assertTrue(d.docs['out']['raises'][0][0].startswith('KeyError'))
        self.assertTrue(d.docs['out']['raises'][0][1].startswith('raises a key'))
        self.assertTrue(d.docs['out']['raises'][1][0].startswith('OtherError'))
        self.assertTrue(d.docs['out']['raises'][1][1].startswith('raises an other'))

    def testGeneratingDocsParams(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        d.generate_docs()
        self.assertTrue(len(d.docs['out']['params']) == 3)
        self.assertTrue(type(d.docs['out']['params'][2]) is tuple)
        self.assertTrue(d.docs['out']['params'][2] == ('third', '', None, '"value"'))
        # param's description
        self.assertTrue(d.docs['out']['params'][1][1].startswith("the 2"))

    def testGeneratingDocsParamsTypeStubs(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc, type_stub=True)
        d.parse_docs()
        d.generate_docs()
        self.assertTrue(':type second: ' in d.docs['out']['raw'])
        self.assertTrue(':type third: ' in d.docs['out']['raw'])

    def testGeneratingGoogleDocsParamsTypeStubs(self):
        doc = googledocs
        d = docs.DocString(myelem, '    ', doc, type_stub=True)
        d.parse_docs()
        d.generate_docs()
        self.assertTrue(':type second: ' in d.docs['out']['raw'])

    def testGeneratingGroupsDocsParamsTypeStubs(self):
        doc = mygrpdocs
        d = docs.DocString(myelem, '    ', doc, type_stub=True)
        d.parse_docs()
        d.generate_docs()
        self.assertTrue(':type first: ' in d.docs['out']['raw'])
        self.assertTrue(':type second: ' in d.docs['out']['raw'])
        self.assertTrue(':type third: ' in d.docs['out']['raw'])

    def testGeneratingGroups2DocsParamsTypeStubs(self):
        doc = mygrpdocs2
        d = docs.DocString(myelem, '    ', doc, type_stub=True)
        d.parse_docs()
        d.generate_docs()
        self.assertTrue(':type first: ' in d.docs['out']['raw'])
        self.assertTrue(':type second: ' in d.docs['out']['raw'])
        self.assertTrue(':type third: ' in d.docs['out']['raw'])

    def testGeneratingNumpyDocsParamsTypeStubs(self):
        doc = mynumpydocs
        d = docs.DocString(myelem, '    ', doc, type_stub=True)
        d.parse_docs()
        d.generate_docs()
        self.assertTrue(':type second: ' in d.docs['out']['raw'])

    def testNoParam(self):
        elem = "    def noparam():"
        doc = """        '''the no param docstring
        '''"""
        d = docs.DocString(elem, '    ', doc, input_style='javadoc')
        d.parse_docs()
        d.generate_docs()
        self.assertFalse(d.docs['out']['params'])

    def testOneLineDocs(self):
        elem = "    def oneline(self):"
        doc = """        '''the one line docstring
        '''"""
        d = docs.DocString(elem, '    ', doc, input_style='javadoc')
        d.parse_docs()
        d.generate_docs()
        #print(d.docs['out']['raw'])
        self.assertFalse(d.docs['out']['raw'].count('\n'))


def main():
    unittest.main()

if __name__ == '__main__':
    main()

