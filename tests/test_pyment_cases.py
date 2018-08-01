#!/usr/bin/python

import unittest
import os
import pyment.pyment as pym
import re

current_dir = os.path.dirname(__file__)
absdir = lambda f: os.path.join(current_dir, f)


def get_expected_patch(self, name):
    """Open a patch file, and if found Pyment signature remove the 2 first lines"""
    try:
        f = open(absdir(name))
        expected = f.readlines()
        if expected[0].startswith("# Patch"):
            expected = expected[2:]
        expected = "".join(expected)
        f.close()
    except Exception as e:
        self.fail('Raised exception: "{0}"'.format(e))
    return expected


def remove_diff_header(diff):
    return re.sub('@@.+@@', '', diff)


class FilesConversionTests(unittest.TestCase):

    def testCaseFreeTesting(self):
        # free cases
        p = pym.PyComment(absdir("free_cases.py"))
        p._parse()
        self.assertTrue(p.parsed)
        result = ''.join(p.diff())
        self.assertTrue(result == '')

    def testCaseGenAllParamsReST(self):
        # The file has several functions with no or several parameters,
        # so Pyment should produce docstrings in reST format
        expected = get_expected_patch(self, "params.py.patch.reST.expected")
        p = pym.PyComment(absdir("params.py"))
        p._parse()
        self.assertTrue(p.parsed)
        result = ''.join(p.diff())
        self.assertTrue(remove_diff_header(result) == remove_diff_header(expected))

    @unittest.expectedFailure
    def testCaseGenAllParamsGoogle(self):
        # The file has several functions with no or several parameters,
        # so Pyment should produce docstrings in google format
        expected = get_expected_patch(self, "params.py.patch.google.expected")
        p = pym.PyComment(absdir("params.py"), output_style="google")
        p._parse()
        self.assertTrue(p.parsed)
        result = ''.join(p.diff())
        self.assertTrue(remove_diff_header(result) == remove_diff_header(expected))

    def testCaseGenAllParamsNumpydoc(self):
        # The file has several functions with no or several parameters,
        # so Pyment should produce docstrings in numpydoc format
        expected = get_expected_patch(self, "params.py.patch.numpydoc.expected")
        p = pym.PyComment(absdir("params.py"), output_style="numpydoc")
        p._parse()
        self.assertTrue(p.parsed)
        result = ''.join(p.diff())
        self.assertTrue(remove_diff_header(result) == remove_diff_header(expected))

    def testCaseGenAllParamsJavadoc(self):
        # The file has several functions with no or several parameters,
        # so Pyment should produce docstrings in javadoc
        expected = get_expected_patch(self, "params.py.patch.javadoc.expected")
        p = pym.PyComment(absdir("params.py"), output_style="javadoc")
        p._parse()
        self.assertTrue(p.parsed)
        result = ''.join(p.diff())
        self.assertTrue(remove_diff_header(result) == remove_diff_header(expected))

    def testCaseNoGenDocsAlreadyReST(self):
        # The file has functions with already docstrings in reST format,
        # so no docstring should be produced
        p = pym.PyComment(absdir("docs_already_reST.py"))
        p._parse()
        self.assertTrue(p.parsed)
        result = ''.join(p.diff())
        self.assertTrue(result == '')

    def testCaseNoGenDocsAlreadyJavadoc(self):
        # The file has functions with already docstrings in javadoc format,
        # so no docstring should be produced
        p = pym.PyComment(absdir("docs_already_javadoc.py"), output_style="javadoc")
        p._parse()
        self.assertTrue(p.parsed)
        result = ''.join(p.diff())
        self.assertTrue(result == '')

    @unittest.expectedFailure
    def testCaseNoGenDocsAlreadyNumpydoc(self):
        # The file has functions with already docstrings in numpydoc format,
        # so no docstring should be produced
        p = pym.PyComment(absdir("docs_already_numpydoc.py"), output_style="numpydoc")
        p._parse()
        self.assertTrue(p.parsed)
        result = ''.join(p.diff())
        self.assertTrue(result == '')

    @unittest.expectedFailure
    def testCaseNoGenDocsAlreadyGoogle(self):
        # The file has functions with already docstrings in google format,
        # so no docstring should be produced
        p = pym.PyComment(absdir("docs_already_google.py"), output_style="google")
        p._parse()
        self.assertTrue(p.parsed)
        result = ''.join(p.diff())
        self.assertTrue(result == '')


def main():
    unittest.main()


if __name__ == '__main__':
    main()
