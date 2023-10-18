"""Module for general management of writing docstrings of multiple files."""

import ast
import os
import platform
import sys
import tempfile
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

from click import echo
from typing_extensions import Self

import pymend.docstring_parser as dsp

from .file_parser import AstAnalyzer
from .output import diff
from .report import Changed
from .types import ElementDocstring, FixerSettings

__author__ = "J-E. Nitschke"
__copyright__ = "Copyright 2012-2021 A. Daouzli"
__licence__ = "GPL3"
__version__ = "1.0.10"
__maintainer__ = "J-E. Nitschke"


@dataclass
class FileContentRepresentation:
    """Container for str and list representation of file contents."""

    lst: list[str]
    lines: str


class Styles(NamedTuple):
    """Container for input and output style."""

    input_style: dsp.DocstringStyle
    output_style: dsp.DocstringStyle


class PyComment:
    """Manage several python scripts docstrings.

    It is used to parse and rewrite in a Pythonic way all the
    functions', methods' and classes' docstrings.
    The changes are then provided in a patch file.
    """

    def __init__(
        self,
        input_file: str,
        *,
        fixer_settings: FixerSettings,
        output_style: dsp.DocstringStyle = dsp.DocstringStyle.NUMPYDOC,
        input_style: dsp.DocstringStyle = dsp.DocstringStyle.AUTO,
        proceed_directly: bool = True,
    ) -> None:
        r"""Set the configuration including the source to proceed and options.

        Parameters
        ----------
        input_file : str
            path name (file or folder)
        fixer_settings : FixerSettings
            Settings for which fixes should be performed.
        output_style : dsp.DocstringStyle
            Output style to use for docstring.
            (Default value = dsp.DocstringStyle.NUMPYDOC)
        input_style : dsp.DocstringStyle
            Input docstring style.
            Auto means that the style is detected automatically. Can cause issues when
            styles are mixed in examples or descriptions."
            (Default value = dsp.DocstringStyle.AUTO)
        proceed_directly : bool
            Whether the file should be parsed directly with the call of
            the constructor. (Default value = True)
        """
        self.input_file = input_file
        self.style = Styles(input_style, output_style)
        input_lines = Path(self.input_file).read_text(encoding="utf-8")
        self._input = FileContentRepresentation(
            input_lines.splitlines(keepends=True), input_lines
        )
        self._output = FileContentRepresentation([], "")
        self.settings = fixer_settings
        self._changed = []
        self.docs_list = []
        self.fixed = False
        if proceed_directly:
            self.proceed()

    def proceed(self) -> None:
        """Parse file and generates/converts the docstrings."""
        self._parse()
        self._compute_before_after()

    def _parse(self) -> list[ElementDocstring]:
        """Parse input file's content and generates a list of its elements/docstrings.

        Returns
        -------
        list[ElementDocstring]
            List of information about module, classes and functions.
        """
        ast_parser = AstAnalyzer(self._input.lines, settings=self.settings)
        self.docs_list = sorted(
            ast_parser.parse_from_ast(), key=lambda element: element.lines
        )
        return self.docs_list

    def _compute_before_after(self) -> tuple[list[str], list[str], list[str]]:
        r"""Compute the before and after and assert equality and stability.

        Make sure that pymend is idempotent.
        Make sure that the original and final Ast's are the same (except for docstring.)

        Returns
        -------
        tuple[list[str], list[str], list[str]]
            Tuple of before, after, changed,
        """
        list_from, list_to, list_changed = self._get_changes()

        self._output.lst = list_to
        self._output.lines = "".join(list_to)
        self._changed = list_changed

        self.assert_stability(list_from, list_to)
        self.assert_equality(self._input.lines, self._output.lines)
        self.fixed = True
        return list_from, list_to, list_changed

    def _get_changes(self) -> tuple[list[str], list[str], list[str]]:
        r"""Compute the list of lines before and after the proposed docstring changes.

        Elements of the list already contain '\n' at the end.

        Returns
        -------
        list_from : list[str]
            Original file as list of lines.
        list_to : list[str]
            Modified content as list of lines.
        list_changed : list[str]
            List of names of elements that were changed.

        Raises
        ------
        ValueError
            If the endline of a docstring was parsed as None.
        """
        list_from = self._input.lst
        list_to: list[str] = []
        list_changed: list[str] = []
        last = 0
        # Loop over all found docstrings and replace the lines where they used to
        # (or ought to) be with the new docstring.
        for e in self.docs_list:
            start, end = e.lines
            if end is None:
                log = self.dump_to_file(
                    "INTERNAL ERROR: End of docstring is None."
                    " Not sure what to do with this yet.",
                    "Original file:.\n",
                    "".join(list_from),
                    "Problematic element:\n",
                    repr(e),
                )
                msg = (
                    "INTERNAL ERROR: End of docstring is None."
                    " Not sure what to do with this yet."
                    " Please report a bug on"
                    " https://github.com/JanEricNitschke/pymend/issues."
                    f" This diff might be helpful: {log}"
                )
                raise ValueError(msg)
            # e.line are line number starting at one.
            # We are now using them to index into a list starting at 0.
            start, end = start - 1, end - 1

            # Grab output docstring and add quotes, indentation and modifiers
            in_docstring = e.docstring
            # Do not need to worry about start being out of range
            # if there was a docstring then it points to that.
            # If there wasnt then there should still be at least one line
            # after the function/class definition. Otherwise that would
            # already have raised an error earlier.
            old_line = list_from[start]
            leading_whitespace = old_line[: -len(old_line.lstrip())]
            trailing_comment = self._get_trailing_comment(list_from[end])
            out_docstring = self._finalizes(
                docstring=e.output_docstring(
                    output_style=self.style.output_style,
                    input_style=self.style.input_style,
                    settings=self.settings,
                ),
                indentation=leading_whitespace,
                modifier=e.modifier,
                trailing=trailing_comment,
            )
            # Check if the docstring changed and if so, add it to the list of changed
            # We can not directly compare with the original out_docstring
            # because that is missing indentation.
            # And it is easiest to add the quotes, modifiers, trailings
            # in one go with the indentation. So for this comparison we have to
            # strip them away again.
            if (
                in_docstring
                != out_docstring.strip()[
                    3 + len(e.modifier) : -(3 + len(trailing_comment))
                ]
            ):
                list_changed.append(e.name)

            # Add all the unchanged things between last and current docstring
            list_to.extend(list_from[last:start])
            # Add the new docstring
            list_to.extend(out_docstring.splitlines(keepends=True))
            # If there was no old docstring then we need to make sure we
            # do not remove the content that was originally on the first line
            # of element.
            if not in_docstring:
                list_to.append(old_line)
            last = end + 1
        # Add the rest of the file.
        if last < len(list_from):
            list_to.extend(list_from[last:])
        return list_from, list_to, list_changed

    def _get_trailing_comment(self, line: str) -> str:
        """Grab any trailing comment that was potentially at the last line.

        Parameters
        ----------
        line : str
            The last line of the docstring.

        Returns
        -------
        str
            The trailing comment
        """
        # This might need some work in the future if there are both
        # types in the same line.
        line = line.strip()
        closing_quotes = max(line.rfind('"""'), line.rfind("'''"))
        if closing_quotes == -1:
            return ""
        return line[closing_quotes + 3 :]

    def _finalizes(
        self,
        docstring: str,
        quotes: str = '"""',
        indentation: str = "    ",
        modifier: str = "",
        trailing: str = "",
    ) -> str:
        r"""Add quotes, indentation and modifiers to the docstring.

        Parameters
        ----------
        docstring : str
            The raw docstring to complete.
        quotes : str
            Quotes to use for the docstring. (Default value = '\"\"\"')
        indentation : str
            How much to indent the docstring lines (Default value = '    ')
        modifier : str
            Modifier to put before the opening triple quotes.
            Any combination of ("r", "f", "u") (Default value = '')
        trailing : str
            Any trailing comment was after the original docstring but on
            the same line. (Default value = '')

        Returns
        -------
        str
            The properly indented docstring, wrapped in triple quotes
            and preceded by the desired modifier.
        """
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
        return "\n".join(split) + trailing + "\n"

    def assert_stability(self, src: list[str], dst: list[str]) -> None:
        """Assert that running pymend on its own output does not change anything.

        Parameters
        ----------
        src : list[str]
            List of lines from the input file.
        dst : list[str]
            List of lines that pymend produced.

        Raises
        ------
        AssertionError
            If a second run of pymend produces a different output than the first.
        """
        # pylint: disable=protected-access
        comment = self.__copy_from_output()
        comment._parse()  # noqa: SLF001
        before, after, changed = comment._get_changes()  # noqa: SLF001
        if changed or not (dst == before and dst == after):
            log = self.dump_to_file(
                "INTERNAL ERROR: PyMend produced different "
                "docstrings on the second pass.\n"
                "Changed:\n",
                "\n".join(changed),
                "".join(diff(src, dst, "source", "first pass")),
                "".join(diff(dst, after, "first pass", "second pass")),
            )
            msg = (
                "INTERNAL ERROR:"
                " PyMend produced different docstrings on the second pass."
                " Please report a bug on"
                " https://github.com/JanEricNitschke/pymend/issues."
                f" This diff might be helpful: {log}"
            )
            raise AssertionError(msg)

    def assert_equality(self, src_lines: str, dst_lines: str) -> None:
        """Assert that running pymend does not change functional ast.

        Done by comparing the asts for the original and produced outputs
        while ignoring the docstrings themselves.

        Parameters
        ----------
        src_lines : str
            Lines from the input file.
        dst_lines : str
            Lines that pymend produced.

        Raises
        ------
        AssertionError
            If the content of the input file could not be parsed into an ast.
        AssertionError
            If the output from pymend could not be parsed into an ast.
        AssertionError
            If the output from pymend produces a different (reduced) ast
            than the input.
        """
        try:
            src_ast = ast.parse(src_lines)
        except Exception as exc:  # noqa: BLE001
            msg = f"Failed to parse source file AST: {exc}\n"
            raise AssertionError(msg) from exc
        try:
            dst_ast = ast.parse(dst_lines)
        except Exception as exc:  # noqa: BLE001
            log = self.dump_to_file(
                "INTERNAL ERROR: PyMend produced invalid code:\n",
                "".join(traceback.format_tb(exc.__traceback__)),
                dst_lines,
            )
            msg = (
                f"INTERNAL ERROR: PyMend produced invalid code: {exc}. "
                "Please report a bug on"
                " https://github.com/JanEricNitschke/pymend/issues."
                f"  This invalid output might be helpful: {log}"
            )
            raise AssertionError(msg) from None
        src_ast_list = self._stringify_ast(src_ast)
        dst_ast_list = self._stringify_ast(dst_ast)
        if src_ast_list != dst_ast_list:
            log = self.dump_to_file(
                "INTERNAL ERROR: PyMend produced code "
                "that is not equivalent to the source\n",
                "".join(diff(src_ast_list, dst_ast_list, "src", "dst")),
            )
            msg = (
                "INTERNAL ERROR: PyMend produced code that is not equivalent to the"
                " source.  Please report a bug on "
                "https://github.com/JanEricNitschke/pymend/issues."
                f"  This diff might be helpful: {log}"
            )
            raise AssertionError(msg) from None

    def __copy_from_output(self) -> Self:
        """Create a new PyComment with the same output style and lines from the input.

        Parameters
        ----------
        lines : list[str]
            List of lines that should make up the `input_lines` of the copied
            instance.

        Returns
        -------
        Self
            The new instance with the same output style and lines initialized
            by the `lines` argument.
        """
        # pylint: disable=protected-access
        py_comment = PyComment.__new__(PyComment)
        py_comment._input = FileContentRepresentation(  # noqa: SLF001
            self._output.lst.copy(), self._output.lines
        )
        py_comment.settings = self.settings
        py_comment._output = FileContentRepresentation([], "")  # noqa: SLF001
        py_comment.style = self.style
        py_comment.docs_list = []
        return py_comment

    def _strip_ast(self, ast_node: ast.AST) -> None:
        """Remove all docstrings from the ast.

        Parameters
        ----------
        ast_node : ast.AST
            Node representing the full ast.
        """
        for node in ast.walk(ast_node):
            # let's work only on functions & classes definitions
            if not isinstance(
                node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef, ast.Module)
            ):
                continue

            if not node.body:
                continue

            if not isinstance(first_element := node.body[0], ast.Expr):
                continue

            if not isinstance(docnode := first_element.value, ast.Constant):
                continue

            if not isinstance(docnode.value, str):
                continue

            node.body = node.body[1:]

    def _stringify_ast(self, node: ast.AST) -> list[str]:
        """Turn ast into string representation with all docstrings removed.

        Parameters
        ----------
        node : ast.AST
            Node to turn into a reduced string representation.

        Returns
        -------
        list[str]
            List of lines making up the reduced string representation.
        """
        self._strip_ast(node)
        return ast.dump(node, indent=1).splitlines(keepends=True)

    def dump_to_file(self, *output: str, ensure_final_newline: bool = True) -> str:
        """Dump `output` to a temporary file. Return path to the file.

        Parameters
        ----------
        *output : str
            List of strings to dump into the output.
        ensure_final_newline : bool
            Whether to make sure that every dumped string
            ends in a new line. (Default value = True)

        Returns
        -------
        str
            Path to the produced temp file.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", prefix="blk_", suffix=".log", delete=False, encoding="utf8"
        ) as f:
            for lines in output:
                f.write(lines)
                if ensure_final_newline and lines and lines[-1] != "\n":
                    f.write("\n")
        return f.name

    def _docstring_diff(self) -> list[str]:
        """Build the diff between original docstring and proposed docstring.

        Returns
        -------
        list[str]
            The resulting diff
        """
        return diff(
            self._input.lst,
            self._output.lst,
            f"a/{self.input_file}",
            f"b/{self.input_file}",
        )

    def output_patch(self) -> Changed:
        """Output the patch. Either to stdout or a file depending on input file.

        Returns
        -------
        Changed
            Whether there were any changes.
        """
        if not self.fixed:
            self.proceed()
        if self._changed:
            lines_to_write = self._get_patch_lines()

            if self.input_file == "-":
                sys.stdout.writelines(lines_to_write)
            else:
                self._write_patch_file(lines_to_write)
        return Changed.YES if bool(self._changed) else Changed.NO

    def output_fix(self) -> Changed:
        """Output the fixed file. Either to stdout or the file.

        Returns
        -------
        Changed
            Whether there were any changes.

        Raises
        ------
        AssertionError
            If the input and output lines are identical but pyment reports
            some elements to have changed.
        """
        if not self.fixed:
            self.proceed()
        if (self._input.lines == self._output.lines) != (len(self._changed) == 0):
            log = self.dump_to_file(
                "INTERNAL ERROR: "
                "Elements having changed does not line up with list of changed "
                "elements.\n",
                "List of changed elements:\n",
                "\n".join(self._changed),
                "Diff\n",
                "".join(self._docstring_diff()),
            )
            msg = (
                "INTERNAL ERROR: "
                "Elements having changed does not line up with list of changed"
                " elements."
                " Please report a bug on"
                " https://github.com/JanEricNitschke/pymend/issues."
                f" This invalid output might be helpful: {log}"
            )
            raise AssertionError(msg)
        if self.input_file == "-":
            sys.stdout.writelines(self._output.lst)
        elif self._input.lines != self._output.lines:
            echo(
                "Modified docstrings of element"
                f'{"s" if len(self._changed) > 1 else ""} '
                f'({", ".join(self._changed)}) in file {self.input_file}.'
            )
            self._overwrite_source_file()
        return Changed.YES if bool(self._changed) else Changed.NO

    def _get_patch_lines(self) -> list[str]:
        r"""Return the diff between source_path and target_path.

        Parameters
        ----------
        source_path : str
            name of the original file (Default value = '')
        target_path : str
            name of the final file (Default value = '')

        Returns
        -------
        list[str]
            the diff as a list of \n terminated lines
        """
        return [
            f"# Patch generated by Pymend v{__version__}\n\n",
            *self._docstring_diff(),
        ]

    def _write_patch_file(self, lines_to_write: list[str]) -> None:
        r"""Write lines_to_write to a the file called patch_file.

        Parameters
        ----------
        lines_to_write : list[str]
            lines to write to the file - they should be \n terminated
        """
        with open(
            f"{os.path.basename(self.input_file)}.patch", "w", encoding="utf-8"
        ) as file:
            file.writelines(lines_to_write)

    def _overwrite_source_file(self) -> None:
        r"""Overwrite the file with line_to_write.

        Parameters
        ----------
        lines_to_write : list[str]
            lines to write to the file - they should be \n terminated
        """
        tmp_filename = f"{self.input_file}.writing"
        ok = False
        try:
            with open(tmp_filename, "w", encoding="utf-8") as file:
                file.writelines(self._output.lines)
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

    def report_issues(self) -> tuple[int, str]:
        """Produce a report of all found issues with the docstrings in the file.

        Returns
        -------
        tuple[int, str]
            The number of elements that had issues as well as
            a string representation of those.
        """
        issues: list[str] = []
        for elem in self.docs_list:
            n_issues, report = elem.report_issues()
            if n_issues:
                issues.append(report)
        if not issues:
            return 0, ""
        report = (
            f"{'*'*50}\nThe following issues were found in file {self.input_file}:\n"
            + "\n".join(issues)
        )
        return len(issues), report
