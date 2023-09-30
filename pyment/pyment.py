"""Module for general management of writing docstrings of multiple files."""

import difflib
import os
import platform
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple, overload

from .file_parser import AstAnalyzer
from .types import ElementDocstring, Style

if TYPE_CHECKING:
    from .docstrings.generators import DocString
    from .docstrings.parsers import DocToolsBase

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
    ) -> None:
        r"""Set the configuration including the source to proceed and options.

        Parameters
        ----------
        input_file : str
            path name (file or folder)
        """
        self.input_file = input_file
        self.input_lines = Path(self.input_file).read_text(encoding="utf-8")
        self.input_style = Style.UNKNOWN
        self.docstring_parser: Optional[DocToolsBase] = None
        self.docstring_generator: Optional[DocString] = None
        self.docs_list = []
        self.parsed = False

    def _starts_with_delimiter(self, line: str) -> bool:
        """Check if line starts with docstring delimiter.

        Parameters
        ----------
        line : str
            Line to check

        Returns
        -------
        bool
            Whether the line starts with a delimiter
        """
        delimiters = ['"""', "'''"]
        modifiers = ["r", "u", "f"]
        if line[:3] in delimiters:
            return True
        if line[0] in modifiers and line[1:4] in delimiters:
            return True
        return line[0] in modifiers and line[1] in modifiers and line[2:5] in delimiters

    def _parse(self) -> List[ElementDocstring]:
        """Parse input file's content and generates a list of its elements/docstrings.

        Returns
        -------
        List[ElementDocstring]
            List of information about module, classes and functions.
        """
        # TODO manage decorators
        ast_parser = AstAnalyzer(self.input_lines)
        self.docs_list = ast_parser.parse_from_ast()
        return self.docs_list

    def get_output_docs(self) -> List:
        """Return the output docstrings once formatted.

        Returns
        -------
        List
            the formatted docstrings
        """
        if not self.parsed:
            self._parse()
        return [e["docs"].get_raw_docs() for e in self.docs_list]

    def compute_before_after(self) -> Tuple[List[str], List[str], List[str]]:
        """Compute the list of lines before and after the proposed docstring changes.

        :return: tuple of before,after where each is a list of lines of python code.

        Returns
        -------
        Tuple[List[str], List[str], List[str]]
            Tuple of before, after, changed,
            where each is a list of lines of python code.
        """
        if not self.parsed:
            self._parse()
        list_from = self.input_lines
        list_to = []
        list_changed = []
        last = 0
        for e in self.docs_list:
            elem_name = e["docs"].element["name"]
            in_docstring = e["docs"].docs["in"]["pure_raw"]
            out_docstring = self.get_stripped_out_docstring(
                e["docs"].docs["out"]["raw"]
            )
            if in_docstring != out_docstring:
                list_changed.append(elem_name)
            start, end = e["location"]
            if start <= 0:
                start, end = -start, -end
                list_to.extend(list_from[last : start + 1])
            else:
                list_to.extend(list_from[last:start])
            docs = e["docs"].get_raw_docs() or ""
            list_docs = [line + "\n" for line in docs.splitlines()]
            list_to.extend(list_docs)
            last = end + 1
        if last < len(list_from):
            list_to.extend(list_from[last:])
        # if not self.module_doc_found:
        #     list_to[self.module_doc_index] = (

        return list_from, list_to, list_changed

    @overload
    def get_stripped_out_docstring(self, doc_string: str) -> str:
        ...

    @overload
    def get_stripped_out_docstring(self, doc_string: None) -> None:
        ...

    def get_stripped_out_docstring(self, doc_string: Optional[str]) -> Optional[str]:
        """Strip and remove docstring quotes from docstring.

        This is the same that is done with the input docstring.
        So do this to be able to directly compare input and output docstrings.

        Parameters
        ----------
        doc_string : str
            Docstring to strip

        Returns
        -------
        str
            Stripped docstring
        """
        if doc_string is None:
            return None
        doc_string = doc_string.strip()
        if doc_string.startswith(('"""', "'''")):
            doc_string = doc_string[3:]
        if doc_string.endswith(('"""', "'''")):
            doc_string = doc_string[:-3]
        return doc_string

    def diff(self, source_path: str = "", target_path: str = "") -> List[str]:
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
        diff_list = difflib.unified_diff(list_from, list_to, fromfile, tofile)
        return list(diff_list)

    def get_patch_lines(self, source_path: str, target_path: str) -> List[str]:
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

    def write_patch_file(self, patch_file: str, lines_to_write: List[str]) -> None:
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

    def overwrite_source_file(self, lines_to_write: List[str]) -> None:
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
        """Parse file and generates/converts the docstrings.

        Returns
        -------
        List[Dict]
            the list of docstrings
        """
        self._parse()
        for element in self.docs_list:
            print(element)
            print(element.docstring)
            element.parse_docstring()
            print(element.produce_output_docstring())
        import sys

        sys.exit()
