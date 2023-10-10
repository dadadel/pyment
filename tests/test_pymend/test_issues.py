"""Testing issues raised on github."""

import os

import pytest

import pymend.pymend as pym
from pymend.types import FixerSettings

current_dir = os.path.dirname(__file__)


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
    return os.path.join(current_dir, file)


class TestIssues:
    """Class for testing raised issues."""

    def test_issue_30(self) -> None:
        """Test issue 30.

        https://github.com/dadadel/pymend/issues/30
        """
        # if file starting with a function/class definition, patching the file
        # will remove the first line!
        comment = pym.PyComment(
            absdir("refs/issue30.py"), fixer_settings=FixerSettings()
        )
        try:
            comment._docstring_diff()
        except Exception as e:  # noqa: BLE001
            pytest.fail(f'Raised exception: "{e}"')

    def test_issue_49(self) -> None:
        """Test issue 49.

        https://github.com/dadadel/pymend/issues/49
        """
        # Title: If already numpydoc format, will remove the Raises section
        # If the last section in a numpydoc docstring is a `Raises` section,
        # it will be removed if the output format is also set to numpydoc
        comment = pym.PyComment(
            absdir("refs/issue49.py"), fixer_settings=FixerSettings()
        )
        result = "".join(comment._docstring_diff())
        assert result == ""
