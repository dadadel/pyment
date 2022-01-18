import shutil
import textwrap
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import pyment.pyment as pym

DATA = Path(__file__).parent / "data"
INIFILE = DATA / "origin_test.py"


from .utils import assert_docstring

@pytest.fixture
def javadoc_file():
    """Returns the path to the javadoc input file."""
    with TemporaryDirectory() as folder:
        path = Path(folder) / "javadoc_file.py"
        shutil.copy(INIFILE, path)
        yield path


@pytest.fixture
def reST_file():
    """Returns the path to the reStructured input file."""
    with TemporaryDirectory() as folder:
        path = Path(folder) / "reST_file.py"
        with open(INIFILE, "r") as ori:
            with open(path, "w") as out:
                out.write(
                    ori.read()
                    .replace("@return", ":returns")
                    .replace("@raise", ":raises")
                    .replace("@", ":")
                )
        yield path


def testParsedJavadoc():
    """ """
    p = pym.PyComment(INIFILE)
    assert len(p._parse()) == 15


def testSameOutJavadocReST(javadoc_file, reST_file):
    """

    Args:
      javadoc_file:
      reST_file:

    Returns:

    Raises:

    """
    assert (
        pym.PyComment(javadoc_file).get_output_docs()
        == pym.PyComment(reST_file).get_output_docs()
    )


def testMultiLinesElements():
    """ """
    p = pym.PyComment(INIFILE)
    p._parse()

    assert_docstring(
        p.get_output_docs()[1],
        """\
        multiline

        :param first:
        :param second:
        :param third:  (Default value = "")

        """,
    )


def testMultiLinesShiftElements():
    """ """
    p = pym.PyComment(INIFILE)
    p._parse()
    assert_docstring(
        p.get_output_docs()[13],
        """\
        there are multilines, shift and kwargs

        :param first:
        :param second:
        :param third:  (Default value = "")
        :param **kwargs:

        """,
    )


def testWindowsRename():
    """ """
    with TemporaryDirectory() as folder:
        bar = Path(folder, "bar")
        foo = Path(folder, "foo")

        with open(bar, "w") as fbar:
            fbar.write("bar")

        with open(foo, "w") as fooo:
            fooo.write("foo")

        assert bar.is_file()
        p = pym.PyComment(foo)
        p._windows_rename(bar)

        assert foo.is_file()

        with open(foo, "r") as fooo:
            foo_txt = fooo.read()
        assert foo_txt == "bar"
