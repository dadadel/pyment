#!/usr/bin/python

import unittest
import os
import pyment.pyment as pym
import pyment.docstring as ds

current_dir = os.path.dirname(__file__)
absdir = lambda f: os.path.join(current_dir, f)


class IssuesTests(unittest.TestCase):

    def testIssue9(self):
        # Title: :rtype: is removed from doc comments; :return: loses indentation
        issue9 = absdir('issue9.py')
        p = pym.PyComment(issue9)
        p._parse()
        self.assertTrue(p.parsed)
        res = p.diff(issue9, "{0}.patch".format(issue9))
        self.assertTrue(res[8].strip() == "-    :return: smthg")
        self.assertTrue(res[9].strip() == "+    :returns: smthg")
        self.assertTrue((res[10][1:].rstrip() == "    :rtype: ret type")
                        and (res[10][0] == ' '))

    def testIssue10(self):
        # Title: created patch-file not correct
        try:
            f = open(absdir("issue10.py.patch.expected"))
            expected = f.read()
            f.close()
        except Exception as e:
            self.fail('Raised exception: "{0}"'.format(e))
        p = pym.PyComment(absdir('issue10.py'))
        p._parse()
        self.assertTrue(p.parsed)
        result = ''.join(p.diff())
        self.assertTrue(result == expected)

    def testIssue11(self):
        # Title: doctests incorrectly formatted with reST option
        deftxt = "def meaning(subject, answer=False):"
        txt = '''"""
    >>> meaning('life', answer=True)
    42
    """'''
        expected = '''    """
    

    :param subject: 
    :param answer:  (Default value = False)

    >>> meaning('life', answer=True)
    42
    """'''
        d = ds.DocString(deftxt, quotes='"""')
        d.parse_docs(txt)
        self.assertTrue(d.get_raw_docs() == expected)

    def testIssue15(self):
        # Title: Does not convert existing docstrings
        try:
            f = open(absdir("issue15.py.patch.expected"))
            expected = f.read()
            f.close()
        except Exception as e:
            self.fail('Raised exception: "{0}"'.format(e))
        p = pym.PyComment(absdir('issue15.py'))
        p._parse()
        self.assertTrue(p.parsed)
        result = ''.join(p.diff())
        self.assertTrue(result == expected)

    def testIssue19(self):
        # Title: :raises in reST is incorrectly parsed
        txt = '''"""

    :raises ValueError: on incorrect JSON
    :raises requests.exceptions.HTTPError: on response error from server
    """'''
        expected = '''    """
    


    :raises ValueError: on incorrect JSON
    :raises requests.exceptions.HTTPError: on response error from server

    """'''
        docs = ds.DocString('def test():', quotes='"""')
        docs.parse_docs(txt)
        self.assertTrue(docs.get_raw_docs() == expected)

    def testIssue30(self):
        # if file starting with a function/class definition, patching the file
        # will remove the first line!
        p = pym.PyComment(absdir('issue30.py'), input_style="numpydoc", output_style="numpydoc")
        p._parse()
        self.assertTrue(p.parsed)
        try:
            p.diff()
        except Exception as e:
            self.fail('Raised exception: "{0}"'.format(e))

    def testIssue32(self):
        # Title: def statement gets deleted
        # if file starting with a function/class definition, patching the file
        # will remove the first line!
        expected = '''--- a/issue32.py
+++ b/issue32.py
@@ -1,2 +1,8 @@
 def hello_world(a=22, b='hello'):
+    """
+
+    :param a:  (Default value = 22)
+    :param b:  (Default value = 'hello')
+
+    """
   return 42'''
        p = pym.PyComment(absdir('issue32.py'))
        p._parse()
        self.assertTrue(p.parsed)
        result = ''.join(p.diff())
        self.assertTrue(result == expected)

    @unittest.expectedFailure
    def testIssue34(self):
        # Title: Problem with regenerating empty param docstring
        # if two consecutive params have empty descriptions, the first will
        # be filled with the full second param line
        p = pym.PyComment(absdir('issue34.py'))
        p._parse()
        self.assertTrue(p.parsed)
        result = ''.join(p.diff())
        self.assertTrue(result == '')

    @unittest.expectedFailure
    def testIssue46(self):
        # Title: list, tuple, dict default param values are not parsed correctly
        # if a list/tuple/dict is given as default value for a parameter, the
        # commas will be considered as separators for parameters
        try:
            f = open(absdir("issue46.py.patch.expected"))
            expected = f.readlines()
            if expected[0].startswith("# Patch"):
                expected = expected[2:]
            expected = "".join(expected)
            f.close()
        except Exception as e:
            self.fail('Raised exception: "{0}"'.format(e))
        p = pym.PyComment(absdir('issue46.py'))
        p._parse()
        self.assertTrue(p.parsed)
        result = ''.join(p.diff())
        self.assertTrue(result == expected)

    @unittest.expectedFailure
    def testIssue47(self):
        # Title:  Extra blank line for docstring with a muli-line description #47
        # If a function has no argument and a multi-line description, Pyment will insert two blank lines
        # between the description and the end of the docstring.
        p = pym.PyComment(absdir('issue47.py'))
        p._parse()
        self.assertTrue(p.parsed)
        result = ''.join(p.diff())
        self.assertTrue(result == '')

    def testIssue49(self):
        # Title: If already numpydoc format, will remove the Raises section
        # If the last section in a numpydoc docstring is a `Raises` section,
        # it will be removed if the output format is also set to numpydoc
        p = pym.PyComment(absdir('issue49.py'), output_style='numpydoc')
        p._parse()
        self.assertTrue(p.parsed)
        result = ''.join(p.diff())
        print(result)
        self.assertTrue(result == '')

    def testIssue58(self):
        # Title: Comments after def statement not supported
        # If a function's def statement is followed by a comment it won't be proceeded.
        p = pym.PyComment(absdir('issue58.py'))
        expected = '''--- a/issue58.py
+++ b/issue58.py
@@ -1,5 +1,9 @@
 def func(param): # some comment
-    """some docstring"""
+    """some docstring
+
+    :param param: 
+
+    """
     pass
 
 
'''
        p._parse()
        self.assertTrue(p.parsed)
        result = ''.join(p.diff())
        self.assertTrue(result == expected)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
