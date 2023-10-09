"""Integration tests of output to numpy format."""

import os
import re

import pytest

import pymend.pymend as pym

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
    """Open a patch file, and if found Pymend signature remove the 2 first lines.

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
    return re.sub(r"(@@.+@@)|(\-\-\-.*)|(\+\+\+.*)", "", diff)


def check_expected_diff(test_name: str) -> None:
    """Check that the patch on source_file equals the expected patch."""
    expected = get_expected_patch(f"{test_name}.py.patch.numpydoc.expected")
    comment = pym.PyComment(absdir(f"refs/{test_name}.py"))
    result = "".join(comment._docstring_diff())
    assert remove_diff_header(result) == remove_diff_header(expected)


class TestNumpyOutput:
    """Integration tests for numpy style output."""

    def test_positional_only_identifier(self) -> None:
        """Make sure that '/' is parsed correctly in signatures."""

    def test_keyword_only_identifier(self) -> None:
        """Make sure that '*' is parsed correctly in signatures."""

    def test_returns(self) -> None:
        """Make sure single and multi return values are parsed/produced correctly."""
        check_expected_diff("returns")

    def test_star_args(self) -> None:
        """Make sure that *args are treated correctly."""

    def test_starstar_kwargs(self) -> None:
        """Make sure that **kwargs are treated correctly."""

    def test_module_doc_dot(self) -> None:
        """Make sure missing '.' are added to the first line of module docstring."""

    def test_ast_ref(self) -> None:
        """Bunch of different stuff."""

    def test_yields(self) -> None:
        """Make sure yields are handled correctly from body."""

    def test_raises(self) -> None:
        """Make sure raises are handled correctly from body."""

    def test_skip_overload(self) -> None:
        """Function annotated with @overload should be skipped for DS creation."""

    def test_class_body(self) -> None:
        """Correctly parse and compose class from body information."""

    def test_quote_default(self) -> None:
        """Test that default values of triple quotes do not cause issues."""
        check_expected_diff("quote_default")
