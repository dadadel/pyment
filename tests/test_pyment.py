#!/usr/bin/python

import unittest
import shutil
import os
import pyment.pyment as pym

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
        @raise KeyError: raises exception

        """'''

current_dir = os.path.dirname(__file__)
absdir = lambda f: os.path.join(current_dir, f)

inifile = absdir('origin_test.py')
jvdfile = absdir('javadoc_test.py')
rstfile = absdir('rest_test.py')


class DocStringTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # prepare test file
        txt = ""
        shutil.copyfile(inifile, jvdfile)
        with open(jvdfile, 'r') as fs:
            txt = fs.read()
        txt = txt.replace("@return", ":returns")
        txt = txt.replace("@raise", ":raises")
        txt = txt.replace("@", ":")
        with open(rstfile, 'w') as ft:
            ft.write(txt)
        print("setup")

    @classmethod
    def tearDownClass(cls):
        os.remove(jvdfile)
        os.remove(rstfile)
        print("end")

    def testParsedJavadoc(self):
        p = pym.PyComment(inifile)
        p._parse()
        self.failUnless(p.parsed)

    def testSameOutJavadocReST(self):
        pj = pym.PyComment(jvdfile)
        pr = pym.PyComment(rstfile)
        pj._parse()
        pr._parse()
        self.assertEqual(pj.get_output_docs(), pr.get_output_docs())

    def testMultiLinesElements(self):
        p = pym.PyComment(inifile)
        p._parse()
        self.failUnless('first' in p.get_output_docs()[1])
        self.failUnless('second' in p.get_output_docs()[1])
        self.failUnless('third' in p.get_output_docs()[1])
        self.failUnless('multiline' in p.get_output_docs()[1])

    def testMultiLinesShiftElements(self):
        p = pym.PyComment(inifile)
        p._parse()
        #TODO: improve this test
        self.assertEqual((len(p.get_output_docs()[13])-len(p.get_output_docs()[13].lstrip())), 8)
        self.failUnless('first' in p.get_output_docs()[13])
        self.failUnless('second' in p.get_output_docs()[13])
        self.failUnless('third' in p.get_output_docs()[13])
        self.failUnless('multiline' in p.get_output_docs()[13])

def main():
    unittest.main()

if __name__ == '__main__':
    main()
