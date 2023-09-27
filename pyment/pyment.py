"""Module for general managment of writing docstrings of multiple files."""

import difflib
import os
import platform
import re
import sys
from typing import Dict, List, Optional, Tuple, TypedDict, overload

from .docstrings.generators import DocString

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


class Element(TypedDict):
    """TypedDict for docstring elements."""

    docs: DocString
    location: Tuple[int, int]


class PyComment:
    """Manage several python scripts docstrings.

    It is used to parse and rewrite in a Pythonic way all the
    functions', methods' and classes' docstrings.
    The changes are then provided in a patch file.
    """

    def __init__(  # noqa: PLR0913
        self,
        input_file: str,
        *,
        input_style: Optional[str] = None,
        quotes: str = '"""',
        convert_only: bool = False,
        config_file: Optional[Dict] = None,
        ignore_private: bool = False,
        indent: int = 2,
    ) -> None:
        r"""Set the configuration including the source to proceed and options.

        Parameters
        ----------
        input_file : str
            path name (file or folder)
        input_style : Optional[str]
            the type of doctrings format of the input. By default, it will autodetect
        quotes : Literal["'''", '\"\"\"']
            the type of quotes to use for output: ''' or \"\"\" (default \"\"\")
        convert_only : bool
            If set only existing docstring will be converted.
            No missing docstring will be created. (Default value = False)
        config_file : Optional[Dict]
            If given configuration file for Pyment (Default value = None)
        ignore_private : bool
            Don't process the private methods/functions
            starting with __ (two underscores) (Default value = False)
        indent : int
            How much each level should be indented. (Default value = 2)
        """
        self.file_type = ".py"
        self.filename_list = []
        self.input_file = input_file
        self.input_lines = []  # Need to remember the file when reading off stdin
        self.input_style = input_style
        self.doc_index = -1
        self.file_index = 0
        self.docs_list = []
        self.parsed = False
        self.quotes = quotes
        self.convert_only = convert_only
        self.config_file = config_file
        self.ignore_private = ignore_private
        self.trailing_space = False
        self.indent = indent
        self.module_doc_index = 0
        self.module_doc_found = False
        self.module_doc_period_missing = False

    def _is_shebang_or_pragma(self, line: str) -> bool:
        """Check if a given line contains encoding or shebang.

        Parameters
        ----------
        line : str
            Line to check

        Returns
        -------
        bool
            Whether the given line contains encoding or shebang
        """
        shebang_regex = r"^#!(.*)"
        if re.search(shebang_regex, line) is not None:
            return True
        pragma_regex = r"^#.*coding[=:]\s*([-\w.]+)"
        return re.search(pragma_regex, line) is not None

    def _starts_with_delimiter(self, line: str) -> bool:
        """Check if line starts with docstring delimeter.

        Parameters
        ----------
        line : str
            Line to check

        Returns
        -------
        bool
            Whether the line starts with a delimeter
        """
        delimeters = ['"""', "'''"]
        modifiers = ["r", "u", "f"]
        if line[:3] in delimeters:
            return True
        if line[0] in modifiers and line[1:4] in delimeters:
            return True
        return line[0] in modifiers and line[1] in modifiers and line[2:5] in delimeters

    def _parse(self) -> List[Element]:  # noqa: PLR0912, PLR0915
        """Parse input file's content and generates a list of its elements/docstrings.

        Returns
        -------
        List[Dict]
            the list of elements
        """
        # TODO manage decorators
        # TODO manage default params with strings escaping chars as (, ), ', ', #, ...
        # TODO manage elements ending with comments like: def func(param): # blabla

        try:
            if self.input_file == "-":
                self.input_lines = sys.stdin.readlines()
            else:
                with open(self.input_file, encoding="utf-8") as folder:
                    self.input_lines = folder.readlines()

        except OSError as exc:
            msg = BaseException(
                f'Failed to open file "{self.input_file}". Please provide a valid file.'
            )
            raise msg from exc

        # Status variables
        # Currently reading a docstring
        reading_docs = None
        # Currently waiting to start the docstring
        waiting_docs = False
        # Currently reading an element and where we are within it
        reading_element = None
        # The (partial) element we are currently reading
        elem = ""
        # How many spaces there are at the start of the docstring (its indentation)
        spaces = ""
        # The raw content of the current docstring
        raw = ""
        # Starting line number of the current docstring
        start = 0
        # Ending line number of the current docstring
        end = 0
        # Modifier for the docstring ['r', 'u', 'f', '']
        before_lim = ""
        # Delimeter used for this docstring ['"""', "'''"]
        lim = '"""'
        # Current list of found elements in this file
        elem_list: List[Element] = []
        # The module docstring has to be within the first three lines
        # Other lines allowed before it are shebang and encoding.
        shebang_encoding_module_doc_string_lines = 3
        for i, full_line in enumerate(self.input_lines):
            line = full_line.strip()
            # Fix or add docstring to beginning of file
            if (
                i < shebang_encoding_module_doc_string_lines
                and not self.module_doc_found
            ):
                if self._is_shebang_or_pragma(full_line):
                    self.module_doc_index = i + 1
                elif full_line.startswith(('"""', "'''")):
                    lim = full_line[:3]
                    self.module_doc_found = True
                    self.module_doc_index = i
                    if line.endswith(lim) and not line.replace(lim, "").endswith("."):
                        self.module_doc_period_missing = True
            if reading_element:
                elem += line
                if line.endswith(":"):
                    reading_element = "end"
            elif (
                line.startswith(("async def ", "def ", "class "))
            ) and not reading_docs:
                if self.ignore_private and line[line.find(" ") :].strip().startswith(
                    "__"
                ):
                    continue
                elem = line
                matched = re.match(
                    r"^(\s*)[adc]", full_line
                )  # a for async, d for def, c for class
                spaces = (
                    matched.group(1)
                    if matched is not None and matched.group(1) is not None
                    else ""
                )
                # the end of definition should be ':' and eventually a comment following
                # FIXME: but this is missing eventual use
                # of '#' inside a string value of parameter
                reading_element = (
                    "end" if re.search(r""":(|\s*#[^'"]*)$""", line) else "start"
                )
            if reading_element == "end":
                reading_element = None
                # if currently reading an element content
                waiting_docs = True
                # *** Creates the DocString object ***
                doc_string = DocString(
                    elem.replace("\n", " "),
                    spaces,
                    quotes=self.quotes,
                    input_style=self.input_style,
                    indent=self.indent,
                )
                elem_list.append({"docs": doc_string, "location": (-i, -i)})
            elif waiting_docs and ('"""' in line or "'''" in line):
                # not docstring
                if not reading_docs and not self._starts_with_delimiter(line):
                    waiting_docs = False
                # start of docstring bloc
                elif not reading_docs:
                    start = i
                    # determine which delimiter
                    idx_c = line.find('"""')
                    idx_dc = line.find("'''")
                    lim = '"""'
                    if idx_c >= 0 and idx_dc >= 0:
                        lim = '"""' if idx_c < idx_dc else "'''"
                    elif idx_c < 0:
                        lim = "'''"
                    reading_docs = lim
                    # check if the docstring starts with 'r', 'u', or 'f'
                    # or combination thus extract it
                    if not line.startswith(lim):
                        idx_strip_lim = line.find(lim)
                        idx_abs_lim = full_line.find(lim)
                        # remove and keep the prefix r|f|u
                        before_lim = line[:idx_strip_lim]
                        full_line = (  # noqa: PLW2901
                            full_line[: idx_abs_lim - idx_strip_lim]
                            + full_line[idx_abs_lim:]
                        )
                    raw = full_line
                    # one line docstring
                    # Both/Two delimiting quotes on one line
                    if line.count(lim) == 2:
                        end = i
                        elem_list[-1]["docs"].parse_docs(raw, before_lim)
                        elem_list[-1]["location"] = (start, end)
                        reading_docs = None
                        waiting_docs = False
                        reading_element = False
                        raw = ""
                # end of docstring bloc
                elif waiting_docs and lim in line:
                    end = i
                    raw += full_line
                    elem_list[-1]["docs"].parse_docs(raw, before_lim)
                    elem_list[-1]["location"] = (start, end)
                    reading_docs = None
                    waiting_docs = False
                    reading_element = False
                    raw = ""
                # inside a docstring bloc
                elif waiting_docs:
                    raw += full_line
            # no docstring found for current element
            elif waiting_docs and line != "" and reading_docs is None:
                waiting_docs = False
            elif reading_docs is not None:
                raw += full_line
        if self.convert_only:
            i = 0
            while i < len(elem_list):
                if elem_list[i]["docs"].get_input_docstring() is None:
                    elem_list.pop(i)
                else:
                    i += 1
        self.docs_list = elem_list
        self.parsed = True
        return elem_list

    def docs_init_to_class(self) -> bool:
        """Move docstring from __init__ to class when sensible.

        If found a __init__ method's docstring and the class.
        without any docstring, so set the class docstring with __init__one,
        and let __init__ without docstring.

        Returns
        -------
        bool
            True if done
        """
        result = False
        if not self.parsed:
            self._parse()
        einit: List[Element] = []
        eclass: List[Element] = []
        for e in self.docs_list:
            if (
                len(eclass) == len(einit) + 1
                and e["docs"].element["name"] == "__init__"
            ):
                einit.append(e)
            elif not eclass and e["docs"].element["deftype"] == "class":
                eclass.append(e)
        for class_element, init_element in zip(eclass, einit):
            start, _ = class_element["location"]
            if start < 0:
                start, _ = init_element["location"]
                if start > 0:
                    result = True
                    cspaces = class_element["docs"].get_spaces()
                    ispaces = init_element["docs"].get_spaces()
                    class_element["docs"].set_spaces(ispaces)
                    init_element["docs"].set_spaces(cspaces)
                    class_element["docs"].generate_docs()
                    init_element["docs"].generate_docs()
                    class_element["docs"], init_element["docs"] = (
                        init_element["docs"],
                        class_element["docs"],
                    )
        return result

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
        if not self.module_doc_found:
            list_to.insert(self.module_doc_index, '"""_summary_."""\n')
            list_changed.insert(0, "Module")
        elif self.module_doc_period_missing:
            module_doc_first_line = list_to[self.module_doc_index]
            lim = module_doc_first_line[:3]
            list_to[self.module_doc_index] = (
                lim + module_doc_first_line.strip().replace(lim, "") + "." + lim + "\n"
            )
            list_changed.insert(0, "Module")

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

    def proceed(self) -> List[Element]:
        """Parse file and generates/converts the docstrings.

        Returns
        -------
        List[Dict]
            the list of docstrings
        """
        self._parse()
        for e in self.docs_list:
            e["docs"].generate_docs()
        return self.docs_list
