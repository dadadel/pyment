"""Module for general management of writing docstrings of multiple files."""

import difflib
import os
import platform
import sys
from pathlib import Path

import pyment.docstring_parser as dsp

from .file_parser import AstAnalyzer
from .types import ElementDocstring

__author__ = "A. Daouzli"
__copyright__ = "Copyright 2012-2021"
__licence__ = "GPL3"
__version__ = "0.4.0dev"
__maintainer__ = "A. Daouzli"

# TODO:
# -generate a return if return is used with argument in element
# -generate raises if raises are used
# -generate diagnosis/statistics
# -parse classes public methods and list them in class docstring
# -allow excluding files from processing
# -add managing a unique patch
# -manage docstrings templates
# -manage c/c++ sources
# -accept archives containing source files
# -dev a server that take sources and send back patches


class PyComment:
    """Manage several python scripts docstrings.

    It is used to parse and rewrite in a Pythonic way all the
    functions', methods' and classes' docstrings.
    The changes are then provided in a patch file.
    """

    def __init__(
        self,
        input_file: str,
        output_style: dsp.DocstringStyle = dsp.DocstringStyle.NUMPYDOC,
    ) -> None:
        r"""Set the configuration including the source to proceed and options.

        Parameters
        ----------
        input_file : str
            path name (file or folder)
        """
        self.input_file = input_file
        self.output_style = output_style
        if self.input_file == "-":
            self.input_lines = sys.stdin.read()
        else:
            self.input_lines = Path(self.input_file).read_text(encoding="utf-8")
        self.docs_list = []
        self.parsed = False

    def _parse(self) -> list[ElementDocstring]:
        """Parse input file's content and generates a list of its elements/docstrings.

        Returns
        -------
        List[ElementDocstring]
            List of information about module, classes and functions.
        """
        # TODO manage decorators
        ast_parser = AstAnalyzer(self.input_lines)
        self.docs_list = sorted(
            ast_parser.parse_from_ast(), key=lambda element: element.lines
        )
        self.parsed = True
        return self.docs_list

    def _get_modifier(self, line: str) -> str:
        """Get the string modifier from the start of a docstring.

        Parameters
        ----------
        line : str
            Line to check

        Returns
        -------
        str
            Modifier(s) of the string.
        """
        line = line.strip()
        delimiters = ['"""', "'''"]
        modifiers = ["r", "u", "f"]
        if not line:
            return ""
        if line[:3] in delimiters:
            return ""
        if line[0] in modifiers and line[1:4] in delimiters:
            return line[0]
        if line[0] in modifiers and line[1] in modifiers and line[2:5] in delimiters:
            return line[:2]
        return ""

    def compute_before_after(self) -> tuple[list[str], list[str], list[str]]:
        """Compute the list of lines before and after the proposed docstring changes.

        Returns
        -------
        Tuple[List[str], List[str], List[str]]
            Tuple of before, after, changed,
            where each is a list of lines of python code.
        """
        if not self.parsed:
            self._parse()
        list_from = self.input_lines.splitlines(keepends=True)
        list_to = []
        list_changed = []
        last = 0
        # Loop over all found docstrings and replace the lines where they used to
        # (or ought to) be with the new docstring.
        for e in self.docs_list:
            start, end = e.lines
            if end is None:
                msg = "End of docstring is None. Not sure what to do with this yet."
                raise ValueError(msg)
            start, end = start - 1, end - 1
            in_docstring = e.docstring
            old_line = list_from[start]
            leading_whitespace = old_line[: -len(old_line.lstrip())]
            modifier = self._get_modifier(old_line)
            raw_out = e.output_docstring(style=self.output_style)
            out_docstring = self._add_quotes_indentation_modifier(
                raw_out,
                indentation=leading_whitespace,
                modifier=modifier,
            )
            if in_docstring != out_docstring.strip()[3:-3]:
                list_changed.append(e.name)
            list_to.extend(list_from[last:start])
            list_to.extend(out_docstring.splitlines(keepends=True))
            if not in_docstring:
                list_to.append(old_line)
            last = end + 1
        if last < len(list_from):
            list_to.extend(list_from[last:])

        return list_from, list_to, list_changed

    def _add_quotes_indentation_modifier(
        self,
        docstring: str,
        quotes: str = '"""',
        indentation: str = "    ",
        modifier: str = "",
    ) -> str:
        split = f"{modifier}{quotes}{docstring}".splitlines()
        # One line docstring get the quotes on the same line
        if len(split) > 1:
            split.append(quotes)
        # Multi-line get them on the next
        else:
            split[0] += quotes
        for index, line in enumerate(split):
            if line.strip():
                split[index] = indentation + line
        return "\n".join(split) + "\n"

    def diff(self, source_path: str = "", target_path: str = "") -> list[str]:
        """Build the diff between original docstring and proposed docstring.

        Parameters
        ----------
        source_path : str
            (Default value = '')
        target_path : str
            (Default value = '')

        Returns
        -------
        List[str]
            the resulted diff
        """
        list_from, list_to, _ = self.compute_before_after()

        if source_path.startswith(os.sep):
            source_path = source_path[1:]
        if source_path and not source_path.endswith(os.sep):
            source_path += os.sep
        if target_path.startswith(os.sep):
            target_path = target_path[1:]
        if target_path and not target_path.endswith(os.sep):
            target_path += os.sep

        fromfile = f"a/{source_path}{os.path.basename(self.input_file)}"
        tofile = f"b/{target_path}{os.path.basename(self.input_file)}"
        diff_lines = []
        for line in difflib.unified_diff(list_from, list_to, fromfile, tofile):
            # Work around https://bugs.python.org/issue2142
            # See:
            # https://www.gnu.org/software/diffutils/manual/html_node/Incomplete-Lines.html
            if line[-1] == "\n":
                diff_lines.append(line)
            else:
                diff_lines.append(line + "\n")
                diff_lines.append("\\ No newline at end of file\n")
        return diff_lines

    def get_patch_lines(self, source_path: str, target_path: str) -> list[str]:
        r"""Return the diff between source_path and target_path.

        Parameters
        ----------
        source_path : str
            name of the original file (Default value = '')
        target_path : str
            name of the final file (Default value = '')

        Returns
        -------
        List[str]
            the diff as a list of \n terminated lines
        """
        diff = self.diff(source_path, target_path)

        return [f"# Patch generated by Pyment v{__version__}\n\n", *diff]

    def write_patch_file(self, patch_file: str, lines_to_write: list[str]) -> None:
        r"""Write lines_to_write to a the file called patch_file.

        Parameters
        ----------
        patch_file : str
            file name of the patch to generate
        lines_to_write : List[str]
            lines to write to the file - they should be \n terminated
        """
        with open(patch_file, "w", encoding="utf-8") as file:
            file.writelines(lines_to_write)

    def overwrite_source_file(self, lines_to_write: list[str]) -> None:
        r"""Overwrite the file with line_to_write.

        Parameters
        ----------
        lines_to_write : List[str]
            lines to write to the file - they should be \n terminated
        """
        tmp_filename = f"{self.input_file}.writing"
        ok = False
        try:
            with open(tmp_filename, "w", encoding="utf-8") as file:
                file.writelines(lines_to_write)
            ok = True
        finally:
            if ok:
                if platform.system() == "Windows":
                    self._windows_rename(tmp_filename)
                else:
                    os.rename(tmp_filename, self.input_file)
            else:
                os.unlink(tmp_filename)

    def _windows_rename(self, tmp_filename: str) -> None:
        """Workaround the fact that os.rename raises an OSError on Windows.

        Parameters
        ----------
        tmp_filename : str
            The file to rename
        """
        if os.path.isfile(self.input_file):
            os.remove(self.input_file)
        os.rename(tmp_filename, self.input_file)

    def proceed(self) -> None:
        """Parse file and generates/converts the docstrings."""
        self._parse()
