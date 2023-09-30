"""Integration tests of output to numpy format."""

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


def check_expected_diff(test_name: str) -> None:
    """Check that the patch on source_file equals the expected patch."""
    expected = get_expected_patch(f"{test_name}.py.patch.numpydoc.expected")
    comment = pym.PyComment(absdir(f"refs/{test_name}.py"))
    comment._parse()
    assert comment.parsed
    result = "".join(comment.diff())
    assert remove_diff_header(result) == remove_diff_header(expected)


class TestNumpyOutput:
    """Integration tests for numpy style output."""

    def test_positional_only_identifier(self) -> None:
        """Make sure that '/' is parsed correctly in signatures."""
        check_expected_diff("positional_only")

    def test_keyword_only_identifier(self) -> None:
        """Make sure that '*' is parsed correctly in signatures."""
        check_expected_diff("keyword_only")

    def test_returns(self) -> None:
        """Make sure single and multi return values are parsed/produced correctly."""
        check_expected_diff("returns")

    def test_star_args(self) -> None:
        """Make sure that *args are treated correctly."""
        check_expected_diff("star_args")

    def test_starstar_kwargs(self) -> None:
        """Make sure that **kwargs are treated correctly."""
        check_expected_diff("star_star_kwargs")

    def test_module_doc_dot(self) -> None:
        """Make sure missing '.' are added to the first line of module docstring."""
        check_expected_diff("module_dot_missing")
