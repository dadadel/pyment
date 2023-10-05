"""Test general pyment functionality."""


import os
import pathlib
import re
import shutil

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


class TestDocStrings:
    """Test correct parsing of docstrings."""

    def setup_class(self) -> None:
        """Set up class by setting file paths."""
        self.myelem = '    def my_method(self, first, second=None, third="value"):'
        self.mydocs = '''        """This is a description of a method.
                It is on several lines.
                Several styles exists:
                    -javadoc,
                    -reST,
                    -cstyle.
                It uses the javadoc style.

                @param first: the 1st argument.
                with multiple lines
                @type first: str
                @param second: the 2nd argument.
                @return: the result value
                @rtype: int
                @raise KeyError: raises exception

                """'''

        self.inifile = absdir("refs/origin_test.py")
        self.jvdfile = absdir("refs/javadoc_test.py")
        self.rstfile = absdir("refs/rest_test.py")
        self.foo = absdir("refs/foo")

        # prepare test file
        txt = ""
        shutil.copyfile(self.inifile, self.jvdfile)
        txt = pathlib.Path(self.jvdfile).read_text()
        txt = txt.replace("@return", ":returns")
        txt = txt.replace("@raise", ":raises")
        txt = txt.replace("@", ":")
        with open(self.rstfile, "w", encoding="utf-8") as rstfile:
            rstfile.write(txt)
        with open(self.foo, "w", encoding="utf-8") as fooo:
            fooo.write("foo")

    def teardown_class(self) -> None:
        """Tear down class by deleting files."""
        os.remove(self.jvdfile)
        os.remove(self.rstfile)
        os.remove(self.foo)

    def test_parsed_javadoc(self) -> None:
        """Test that javadoc comments get parsed."""
        comment = pym.PyComment(self.inifile)
        comment._parse()
        assert comment.parsed

    def test_windows_rename(self) -> None:
        """Check that renaming works correctly."""
        bar = absdir("bar")
        with open(bar, "w", encoding="utf-8") as fbar:
            fbar.write("bar")
        comment = pym.PyComment(self.foo)
        comment._windows_rename(bar)
        assert not os.path.isfile(bar)
        assert os.path.isfile(self.foo)
        foo_txt = pathlib.Path(self.foo).read_text()
        assert foo_txt == "bar"


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
