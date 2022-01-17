#!/usr/bin/python

import pytest
import os
import pyment.pyment as pym
import pyment.docstring as ds

from .utils import assert_docstring

current_dir = os.path.dirname(__file__)
absdir = lambda f: os.path.join(current_dir, f)


def testIssue9():
    # Title: :rtype: is removed from doc comments; :return: loses indentation
    issue9 = absdir("issue9.py")
    p = pym.PyComment(issue9)
    p._parse()
    assert p.parsed
    res = p.diff(issue9, "{0}.patch".format(issue9))
    assert res[8].strip() == "-    :return: smthg"
    assert res[9].strip() == "+    :returns: smthg"
    assert (res[10][1:].rstrip() == "    :rtype: ret type") and (res[10][0] == " ")


def testIssue10():
    # Title: created patch-file not correct
    try:
        f = open(absdir("issue10.py.patch.expected"))
        expected = f.read()
        f.close()
    except Exception as e:
        self.fail('Raised exception: "{0}"'.format(e))
    p = pym.PyComment(absdir("issue10.py"))
    p._parse()
    assert p.parsed
    result = "".join(p.diff())
    assert result == expected


def testIssue11():
    # Title: doctests incorrectly formatted with reST option
    deftxt = "def meaning(subject, answer=False):"
    txt = '''"""
>>> meaning('life', answer=True)
42
"""'''
    d = ds.DocString(deftxt, quotes='"""')
    d.parse_docs(txt)
    assert_docstring(
        d.get_raw_docs(),
        """    
    

    :param subject: 
    :param answer:  (Default value = False)

    >>> meaning('life', answer=True)
    42
    """,
    )


def testIssue15():
    # Title: Does not convert existing docstrings
    p = pym.PyComment(absdir("issue15.py"))
    p._parse()
    assert p.parsed
    result = "".join(p.diff())

    with open(absdir("issue15.py.patch.expected")) as f:
        expected = f.read()
    assert result == expected


def testIssue19_work():
    # Title: :raises in reST is incorrectly parsed
    txt = '''"""

    :raises ValueError: on incorrect JSON
    :raises requests.exceptions.HTTPError: on response error from server
    """'''
    expected = '''    """
    


    :raises ValueError: on incorrect JSON
    :raises requests.exceptions.HTTPError: on response error from server

    """'''
    docs = ds.DocString("def test():", quotes='"""')
    docs.parse_docs(txt)
    assert docs.get_raw_docs() == expected


def testIssue22():
    # Title: Class __init__() docstrings are not generated
    expected = '''--- a/issue22.py
+++ b/issue22.py
@@ -2,4 +2,9 @@
     """Test class for issue 22"""
 
     def __init__(self, param1):
+        """
+
+        :param param1: 
+
+        """
         pass
'''
    p = pym.PyComment(absdir("issue22.py"))
    p._parse()
    assert p.parsed
    result = "".join(p.diff())
    assert result == expected


def testIssue30():
    # if file starting with a function/class definition, patching the file
    # will remove the first line!
    p = pym.PyComment(
        absdir("issue30.py"), input_style="numpydoc", output_style="numpydoc"
    )
    p._parse()
    assert p.parsed
    assert p.diff() == [
        "--- a/issue30.py\n",
        "+++ b/issue30.py\n",
        "@@ -1,2 +1,16 @@\n",
        " def hello_world(a=22, b='hello'):\n",
        '+    """\n',
        "+\n",
        "+    Parameters\n",
        "+    ----------\n",
        "+    a :\n",
        "+         (Default value = 22)\n",
        "+    b :\n",
        "+         (Default value = 'hello')\n",
        "+\n",
        "+    Returns\n",
        "+    -------\n",
        "+\n",
        "+    \n",
        '+    """\n',
        "   return 42",
    ]


def testIssue32():
    # Title: def statement gets deleted
    # if file starting with a function/class definition, patching the file
    # will remove the first line!
    expected = '''--- a/issue32.py
+++ b/issue32.py
@@ -1,2 +1,8 @@
 def hello_world(a=22, b='hello'):
+    """
+
+    :param a:  (Default value = 22)
+    :param b:  (Default value = 'hello')
+
+    """
   return 42'''
    p = pym.PyComment(absdir("issue32.py"))
    p._parse()
    assert p.parsed
    result = "".join(p.diff())
    assert result == expected


def testIssue34():
    # Title: Problem with regenerating empty param docstring
    # if two consecutive params have empty descriptions, the first will
    # be filled with the full second param line
    p = pym.PyComment(absdir("issue34.py"))
    with pytest.raises(TypeError):
        p._parse()


def testIssue46():
    # Title: list, tuple, dict default param values are not parsed correctly
    # if a list/tuple/dict is given as default value for a parameter, the
    # commas will be considered as separators for parameters
    with open(absdir("issue46.py.patch.expected")) as f:
        expected = f.readlines()
        if expected[0].startswith("# Patch"):
            expected = expected[2:]
        expected = "".join(expected)
    p = pym.PyComment(absdir("issue46.py"))
    p._parse()
    assert p.parsed
    result = "".join(p.diff())
    assert result == expected


def testIssue47():
    # Title:  Extra blank line for docstring with a muli-line description #47
    # If a function has no argument and a multi-line description, Pyment will insert two blank lines
    # between the description and the end of the docstring.
    p = pym.PyComment(absdir("issue47.py"))
    p._parse()
    assert p.parsed
    result = "".join(p.diff())

    with pytest.raises(AssertionError):
        assert result == ""


def testIssue49():
    # Title: If already numpydoc format, will remove the Raises section
    # If the last section in a numpydoc docstring is a `Raises` section,
    # it will be removed if the output format is also set to numpydoc
    p = pym.PyComment(absdir("issue49.py"), output_style="numpydoc")
    p._parse()
    assert p.parsed
    result = "".join(p.diff())
    assert result == ""


def testIssue51():
    # Title:  Raise block convertion
    p = pym.PyComment(absdir("issue51.py"), output_style="google")
    p._parse()
    assert p.parsed
    result = "".join(p.diff())
    assert result == ""


def testIssue58():
    # Title: Comments after def statement not supported
    # If a function's def statement is followed by a comment it won't be proceeded.
    p = pym.PyComment(absdir("issue58.py"))
    expected = '''--- a/issue58.py
+++ b/issue58.py
@@ -1,5 +1,9 @@
 def func(param): # some comment
-    """some docstring"""
+    """some docstring
+
+    :param param: 
+
+    """
     pass
 
 
'''
    p._parse()
    assert p.parsed
    result = "".join(p.diff())
    assert result == expected


def testIssue69():
    # Title: Wrong Formatting for Input params with default values
    # When default value has a list it is split and considers list's elements as parameters
    p = pym.PyComment(absdir("issue69.py"))
    p._parse()
    with open(absdir("issue69.py.patch")) as f:
        patch = f.read()
    assert "".join(p.diff()) == patch


def testIssue85():
    # Title: When converting from reST, parameter types are not handled correctly
    # For reST, Sphinx allows to declare the type inside the parameter statement
    # like this: `:param str name: description`
    # Pyment should support this.
    p = pym.PyComment(absdir("issue85.py"))
    p._parse()
    with open(absdir("issue85.py.patch")) as f:
        patch = f.read()
    assert "".join(p.diff()) == patch


def testIssue88():
    # Title: Not working on async functions
    # The async functions are not managed
    p = pym.PyComment(absdir("issue88.py"))
    p._parse()
    with open(absdir("issue88.py.patch")) as f:
        patch = f.read()
    assert "".join(p.diff()) == patch


def testIssue90():
    # Title: __doc__ is not well parsed
    # If the line after function signature contains triple [double] quotes but is not a docstring
    # it will be however considered as if it was and will have side effect.
    p = pym.PyComment(absdir("issue90.py"))
    p._parse()
    with open(absdir("issue90.py.patch")) as f:
        patch = f.read()
    assert "".join(p.diff()) == patch


def testIssue93():
    # Title: Support for type hints
    # Add support for type hints (PEP 484).
    p = pym.PyComment(absdir("issue93.py"))
    p._parse()
    with open(absdir("issue93.py.patch")) as f:
        patch = f.read()
    assert "".join(p.diff()) == patch


def testIssue95():
    # Title: When there's a parameter without description in reST, Pyment copies the whole next element
    p = pym.PyComment(absdir("issue95.py"))
    p._parse()
    with open(absdir("issue95.py.patch")) as f:
        patch = f.read()
    assert "".join(p.diff()) == patch


def testIssue99():
    # Title: Type is removed from parameter if not in type hints when converting reST docstring
    p = pym.PyComment(absdir("issue99.py"))
    p._parse()
    with open(absdir("issue99.py.patch")) as f:
        patch = f.read()
    assert "".join(p.diff()) == patch
