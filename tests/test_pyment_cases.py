import os
import re

import pytest

import pyment.pyment as pym

current_dir = os.path.dirname(__file__)
absdir = lambda f: os.path.join(current_dir, f)


def get_expected_patch(name):
    """Open a patch file, and if found Pyment signature remove the 2 first lines"""
    with open(absdir(name)) as f:
        expected = f.readlines()
        if expected[0].startswith("# Patch"):
            expected = expected[2:]
        expected = "".join(expected)
    return expected


def remove_diff_header(diff):
    return re.sub("@@.+@@", "", diff)


def testCaseFreeTesting():
    # free cases
    p = pym.PyComment(absdir("free_cases.py"))
    p._parse()
    assert p.parsed
    result = "".join(p.diff())
    assert result == ""


def testCaseGenAllParamsReST():
    # The file has several functions with no or several parameters,
    # so Pyment should produce docstrings in reST format
    expected = get_expected_patch("params.py.patch.reST.expected")
    p = pym.PyComment(absdir("params.py"))
    p._parse()
    assert p.parsed
    result = "".join(p.diff())
    assert remove_diff_header(result) == remove_diff_header(expected)


def testCaseGenAllParamsGoogle():
    # The file has several functions with no or several parameters,
    # so Pyment should produce docstrings in google format
    expected = get_expected_patch("params.py.patch.google.expected")
    p = pym.PyComment(absdir("params.py"), output_style="google")
    p._parse()
    assert p.parsed
    result = "".join(p.diff())
    with pytest.raises(AssertionError):
        assert remove_diff_header(result) == remove_diff_header(expected)


def testCaseGenAllParamsNumpydoc():
    # The file has several functions with no or several parameters,
    # so Pyment should produce docstrings in numpydoc format
    expected = get_expected_patch("params.py.patch.numpydoc.expected")
    p = pym.PyComment(absdir("params.py"), output_style="numpydoc")
    p._parse()
    assert p.parsed
    result = "".join(p.diff())
    assert remove_diff_header(result) == remove_diff_header(expected)


def testCaseGenAllParamsJavadoc():
    # The file has several functions with no or several parameters,
    # so Pyment should produce docstrings in javadoc
    expected = get_expected_patch("params.py.patch.javadoc.expected")
    p = pym.PyComment(absdir("params.py"), output_style="javadoc")
    p._parse()
    assert p.parsed
    result = "".join(p.diff())
    assert remove_diff_header(result) == remove_diff_header(expected)


def testCaseNoGenDocsAlreadyReST():
    # The file has functions with already docstrings in reST format,
    # so no docstring should be produced
    p = pym.PyComment(absdir("docs_already_reST.py"))
    p._parse()
    assert p.parsed
    result = "".join(p.diff())
    assert result == ""


def testCaseNoGenDocsAlreadyJavadoc():
    # The file has functions with already docstrings in javadoc format,
    # so no docstring should be produced
    p = pym.PyComment(absdir("docs_already_javadoc.py"), output_style="javadoc")
    p._parse()
    assert p.parsed
    result = "".join(p.diff())
    assert result == ""


def testCaseNoGenDocsAlreadyNumpydoc():
    # The file has functions with already docstrings in numpydoc format,
    # so no docstring should be produced
    p = pym.PyComment(absdir("docs_already_numpydoc.py"), output_style="numpydoc")
    p._parse()
    assert p.parsed
    result = "".join(p.diff())
    with pytest.raises(AssertionError):
        assert result == ""


def testCaseNoGenDocsAlreadyGoogle():
    # The file has functions with already docstrings in google format,
    # so no docstring should be produced
    p = pym.PyComment(absdir("docs_already_google.py"), output_style="google")
    p._parse()
    assert p.parsed
    result = "".join(p.diff())
    with pytest.raises(AssertionError):
        assert result == ""
