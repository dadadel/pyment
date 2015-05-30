#!/usr/bin/python

import unittest
import shutil
import os
import pyment.pyment as pym

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


def main():
    unittest.main()

if __name__ == '__main__':
    main()
