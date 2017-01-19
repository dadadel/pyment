#!/usr/bin/python

import unittest
import os
import pyment.pyment as pym
import pyment.docstring as ds

current_dir = os.path.dirname(__file__)
absdir = lambda f: os.path.join(current_dir, f)


class IssuesTests(unittest.TestCase):

    def testIssue9(self):
        issue9 = absdir('issue9.py')
        p = pym.PyComment(issue9)
        p._parse()
        self.assertTrue(p.parsed)
        res = p.diff(issue9, "{0}.patch".format(issue9))
        self.assertTrue(res[8].strip() != "-    :return: smthg")
        self.assertTrue(res[9].strip() != "-    :rtype: ret type")
        self.assertTrue(res[10].strip() != "+:return: smthg")

    def testIssue11(self):
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

    def testIssue19(self):
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

    def testIssue32(self):
        # if file starting with a function/class definition, patching the file
        # will remove the first line!
        expected = """--- a/issue32.py
+++ b/issue32.py
@@ -1,2 +1,8 @@
 def hello_world(a=22, b='hello'):
+    '''
+
+    :param a:  (Default value = 22)
+    :param b:  (Default value = 'hello')
+
+    '''
   return 42"""
        p = pym.PyComment(absdir('issue32.py'))
        p._parse()
        self.assertTrue(p.parsed)
        result = ''.join(p.diff())
        self.assertTrue(result == expected)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
