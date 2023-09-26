#!/usr/bin/python

import os
import pyment.pyment as pym
import pyment.docstring as ds

current_dir = os.path.dirname(__file__)
absdir = lambda f: os.path.join(current_dir, f)


class TestIssues:
    def test_issue_30(self):
        # if file starting with a function/class definition, patching the file
        # will remove the first line!
        p = pym.PyComment(
            absdir("issue30.py"), input_style="numpydoc", output_style="numpydoc"
        )
        p._parse()
        assert p.parsed
        try:
            p.diff()
        except Exception as e:
            self.fail('Raised exception: "{0}"'.format(e))

    def test_issue_49(self):
        # Title: If already numpydoc format, will remove the Raises section
        # If the last section in a numpydoc docstring is a `Raises` section,
        # it will be removed if the output format is also set to numpydoc
        p = pym.PyComment(absdir("issue49.py"), output_style="numpydoc")
        p._parse()
        assert p.parsed
        result = "".join(p.diff())
        print(result)
        assert result == ""
