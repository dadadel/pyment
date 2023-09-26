#!/usr/bin/python

import os
import pyment.pyment as pym
import re
import pytest

CURRENT_DIR = os.path.dirname(__file__)
def absdir(f):
    return os.path.join(CURRENT_DIR, f)


def get_expected_patch(self, name):
    """Open a patch file, and if found Pyment signature remove the 2 first lines"""
    try:
        f = open(absdir(f"refs/{name}"))
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


class TestFilesConversions:

    def test_case_free_testing(self):
        # free cases
        p = pym.PyComment(absdir("refs/free_cases.py"))
        p._parse()
        assert p.parsed
        result = ''.join(p.diff())
        assert result == ''



    def test_case_gen_all_params_numpydoc(self):
        # The file has several functions with no or several parameters,
        # so Pyment should produce docstrings in numpydoc format
        expected = get_expected_patch(self, "params.py.patch.numpydoc.expected")
        p = pym.PyComment(absdir("refs/params.py"), output_style="numpydoc")
        p._parse()
        assert p.parsed
        result = ''.join(p.diff())
        assert remove_diff_header(result) == remove_diff_header(expected)



    def test_case_no_gen_docs_already_numpydoc(self):
        # The file has functions with already docstrings in numpydoc format,
        # so no docstring should be produced
        p = pym.PyComment(absdir("refs/docs_already_numpydoc.py"), output_style="numpydoc")
        p._parse()
        assert p.parsed
        result = ''.join(p.diff())
        assert result == ''

