"""Module to test general pyment functionality."""


import os
import re

import pytest

import pyment.pyment as pym

CURRENT_DIR = os.path.dirname(__file__)


def absdir(file: str) -> str:
    """Get absolute path for file.

    Parameters
    ----------
    file : str
        File path

    Returns
    -------
    str
        Absolute path to file
    """
    return os.path.join(CURRENT_DIR, file)


def get_expected_patch(name: str) -> str:
    """Open a patch file, and if found Pyment signature remove the 2 first lines.

    Parameters
    ----------
    name : str
        Name of the patch

    Returns
    -------
    str
        Expected patch as a string.
    """
    try:
        with open(absdir(f"refs/{name}"), encoding="utf-8") as file:
            expected_lines = file.readlines()
            if expected_lines[0].startswith("# Patch"):
                expected_lines = expected_lines[2:]
            expected = "".join(expected_lines)
    except Exception as error:  # noqa: BLE001
        pytest.fail(f'Raised exception: "{error}"')
    return expected


def remove_diff_header(diff: str) -> str:
    """Remove header differences from diff.

    Parameters
    ----------
    diff : str
        Diff file to clean.

    Returns
    -------
    str
        Cleaned diff.
    """
    return re.sub("@@.+@@", "", diff)


class TestFilesConversions:
    """Test patch files."""

    def test_case_free_testing(self) -> None:
        """Test correct handling for case where input style in ambiguous."""
        comment = pym.PyComment(absdir("refs/free_cases.py"))
        comment._parse()
        assert comment.parsed
        result = "".join(comment.diff())
        assert result == ""

    def test_case_gen_all_params_numpydoc(self) -> None:
        """Test generation of numpydoc patch.

        The file has several functions with no or several parameters,
        so Pyment should produce docstrings in numpydoc format.
        """
        expected = get_expected_patch("params.py.patch.numpydoc.expected")
        comment = pym.PyComment(absdir("refs/params.py"))
        comment._parse()
        assert comment.parsed
        result = "".join(comment.diff())
        assert remove_diff_header(result) == remove_diff_header(expected)

    def test_case_no_gen_docs_already_numpydoc(self) -> None:
        """Test that correct format needs no fixing.

        The file has functions with already docstrings in numpydoc format,
        so no docstring should be produced.
        """
        comment = pym.PyComment(absdir("refs/docs_already_numpydoc.py"))
        comment._parse()
        assert comment.parsed
        result = "".join(comment.diff())
        assert result == ""
