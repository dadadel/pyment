"""Module for general management of writing docstrings of multiple files."""

import ast
import difflib
import os
import platform
import sys
import tempfile
import traceback
from pathlib import Path

from typing_extensions import Self

import pymend.docstring_parser as dsp

from .file_parser import AstAnalyzer
from .types import ElementDocstring

__author__ = "J-E. Nitschke"
__copyright__ = "Copyright 2012-2021 A. Daouzli"
__licence__ = "GPL3"
__version__ = "1.0.0"
__maintainer__ = "J-E. Nitschke"


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
        output_style : dsp.DocstringStyle
            Output style to use for docstring.
            (Default value = dsp.DocstringStyle.NUMPYDOC)
        """
        self.input_file = input_file
        self.output_style = output_style
        if self.input_file == "-":
            self.input_lines = sys.stdin.read()
        else:
            self.input_lines = Path(self.input_file).read_text(encoding="utf-8")
        self.docs_list = []
        self.parsed = False

    def __copy_from_line_list(self, lines: list[str]) -> Self:
        py_comment = PyComment.__new__(PyComment)
        py_comment.input_lines = "".join(lines)
        py_comment.output_style = self.output_style
        py_comment.parsed = False
        py_comment.docs_list = []
        return py_comment

    def _parse(self) -> list[ElementDocstring]:
        """Parse input file's content and generates a list of its elements/docstrings.

        Returns
        -------
        List[ElementDocstring]
            List of information about module, classes and functions.
        """
        ast_parser = AstAnalyzer(self.input_lines)
        self.docs_list = sorted(
            ast_parser.parse_from_ast(), key=lambda element: element.lines
        )
        self.parsed = True
        return self.docs_list

    def get_changes(self) -> tuple[list[str], list[str], list[str]]:
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
        """
        if not self.parsed:
            self._parse()
        list_from = self.input_lines.splitlines(keepends=True)
        list_to: list[str] = []
        list_changed: list[str] = []
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
            raw_out = e.output_docstring(style=self.output_style)
            out_docstring = self._add_quotes_indentation_modifier(
                raw_out,
                indentation=leading_whitespace,
                modifier=e.modifier,
            )
            if in_docstring != out_docstring.strip()[3 + len(e.modifier) : -3]:
                list_changed.append(e.name)
            list_to.extend(list_from[last:start])
            list_to.extend(out_docstring.splitlines(keepends=True))
            if not in_docstring:
                list_to.append(old_line)
            last = end + 1
        if last < len(list_from):
            list_to.extend(list_from[last:])
        return list_from, list_to, list_changed

    def compute_before_after(self) -> tuple[list[str], list[str], list[str]]:
        r"""Compute the before and after and assert equality and stability.

        Make sure that pymend is idempotent.
        Make sure that the original and final Ast's are the same (except for docstring.)

        Returns
        -------
        Tuple[List[str], List[str], List[str]]
            Tuple of before, after, changed,
        """
        list_from, list_to, list_changed = self.get_changes()
        self.assert_stability(list_from, list_to)
        self.assert_equality(list_from, list_to)
        return list_from, list_to, list_changed

    def assert_stability(self, src: list[str], dst: list[str]) -> None:
        """Assert that running pymend on its own output does not change anything."""
        comment = self.__copy_from_line_list(dst)
        comment.proceed()
        before, after, changed = comment.get_changes()
        if changed or not (dst == before and dst == after):
            log = self.dump_to_file(
                "Changed:\n",
                "\n".join(changed),
                "".join(self._pure_diff(src, dst, "source", "first pass")),
                "".join(self._pure_diff(dst, after, "first pass", "second pass")),
            )
            msg = (
                "INTERNAL ERROR:"
                " PyMend produced docstrings on the second pass."
                " Please report a bug on"
                " https://github.com/JanEricNitschke/pymend/issues."
                f"  This diff might be helpful: {log}"
            )
            raise AssertionError(msg)

    def assert_equality(self, src: list[str], dst: list[str]) -> None:
        """Assert that running pymend does not change functional ast.

        Done by comparing the asts for the original and produced outputs
        while ignoring the docstrings themselves.
        """
        src_lines = "".join(src)
        dst_lines = "".join(dst)
        try:
            src_ast = ast.parse(src_lines)
        except Exception as exc:  # noqa: BLE001
            msg = f"Failed to parse source file AST: {exc}\n"
            raise AssertionError(msg) from exc
        try:
            dst_ast = ast.parse(dst_lines)
        except Exception as exc:  # noqa: BLE001
            log = self.dump_to_file(
                "".join(traceback.format_tb(exc.__traceback__)), dst_lines
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
                "".join(self._pure_diff(src_ast_list, dst_ast_list, "src", "dst"))
            )
            msg = (
                "INTERNAL ERROR: PyMend produced code that is not equivalent to the"
                " source.  Please report a bug on "
                "https://github.com/JanEricNitschke/pymend/issues."
                f"  This diff might be helpful: {log}"
            )
            raise AssertionError(msg) from None

    def _strip_ast(self, ast_node: ast.AST) -> None:
        """Remove all docstrings from the ast."""
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
        """Turn ast into string representation with all docstrings removed."""
        self._strip_ast(node)
        return ast.dump(node, indent=1).splitlines(keepends=True)

    def dump_to_file(self, *output: str, ensure_final_newline: bool = True) -> str:
        """Dump `output` to a temporary file. Return path to the file."""
        with tempfile.NamedTemporaryFile(
            mode="w", prefix="blk_", suffix=".log", delete=False, encoding="utf8"
        ) as f:
            for lines in output:
                f.write(lines)
                if ensure_final_newline and lines and lines[-1] != "\n":
                    f.write("\n")
        return f.name

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

        fromfile = f"a/{source_path}"
        tofile = f"b/{target_path}"
        return self._pure_diff(list_from, list_to, fromfile, tofile)

    def _pure_diff(
        self,
        src: list[str],
        dst: list[str],
        source_path: str = "",
        target_path: str = "",
    ) -> list[str]:
        diff_lines: list[str] = []
        for line in difflib.unified_diff(src, dst, source_path, target_path):
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

        return [f"# Patch generated by Pymend v{__version__}\n\n", *diff]

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
