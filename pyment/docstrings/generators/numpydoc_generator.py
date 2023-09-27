"""Module for generating numpy docstrings."""

import re
from typing import Dict, List, Optional, TypedDict

from pyment.docstrings.parsers import Docs, DocsTools
from pyment.docstrings.parsers.manager import Params

__author__ = "J. Nitschke"
__copyright__ = "Copyright 2012-2018, A. Daouzli"
__licence__ = "GPL3"
__version__ = "0.3.18"
__maintainer__ = "J. Nitschke"

"""
Formats supported at the time:
 - javadoc, reST (restructured text, Sphinx):
 managed  -> description, param, type, return, rtype, raise
 - google:
 managed  -> description, parameters, return, raises
 - numpydoc:
 managed  -> description, parameters, return (first of list only), raises

"""


class Signatures(TypedDict):
    """Typedict for function signatures."""

    parameters: Dict[int, Params]
    return_type: str


class DocStringElement(TypedDict):
    """Typeddict for docstring elements."""

    raw: str
    name: Optional[str]
    deftype: Optional[str]
    type: Optional[str]
    params: List[Params]
    spaces: str
    rtype: Optional[str]


class DocString:
    """Represents the docstring."""

    def __init__(  # noqa: PLR0913
        self,
        elem_raw: str,
        spaces: str = "",
        docs_raw: Optional[str] = None,
        quotes: str = "'''",
        input_style: Optional[str] = None,
        *,
        before_lim: str = "",
        indent: int = 2,
    ) -> None:
        """_summary_.

        Parameters
        ----------
        elem_raw : str
            raw data of the element (def or class).
        spaces : str
            the leading whitespaces before the element (Default value = "")
        docs_raw : Optional[str]
            the raw data of the docstring part if any. (Default value = None)
        quotes : str
            the type of quotes to use for output: ' ' ' or " " " (Default value = "'''")
        input_style : Optional[str]
            _description_ (Default value = None)
        before_lim : str
            specify raw or unicode or format docstring type
            (ie. "r" for r'''... or "fu" for fu'''...) (Default value = "")
        indent : int
            _description_ (Default value = 2)
        """
        self.dst = DocsTools()
        self.before_lim = before_lim
        if docs_raw and not input_style:
            self.dst.autodetect_style(docs_raw)
        elif input_style:
            self.set_input_style(input_style)
        self.element: DocStringElement = {
            "raw": elem_raw,
            "name": None,
            "deftype": None,
            "type": None,
            "params": [],
            "spaces": spaces,
            "rtype": None,
        }
        docs_raw = docs_raw or ""
        if docs_raw:
            docs_raw = docs_raw.strip()
            if docs_raw.startswith(('"""', "'''")):
                docs_raw = docs_raw[3:]
            if docs_raw.endswith(('"""', "'''")):
                docs_raw = docs_raw[:-3]
        self.docs: Docs = {
            "in": {
                "raw": docs_raw,
                "pure_raw": docs_raw,
                "doctests": "",
                "desc": None,
                "params": [],
                "types": [],
                "return": None,
                "rtype": None,
                "raises": [],
            },
            "out": {
                "raw": "",
                "desc": None,
                "params": [],
                "types": [],
                "return": None,
                "rtype": None,
                "raises": [],
                "spaces": spaces + " " * indent,
            },
        }
        if "\t" in spaces:
            self.docs["out"]["spaces"] = spaces + "\t"
        elif (len(spaces) % 4) == 0 or not spaces:
            # FIXME: should bug if tabs for class or function (as spaces=='')
            self.docs["out"]["spaces"] = spaces + " " * 4
        self.parsed_elem = False
        self.parsed_docs = False
        self.generated_docs = False
        self._options = {
            "hint_rtype_priority": True,  # priority in type hint else in docstring
            "hint_type_priority": True,  # priority in type hint else in docstring
            # in reST docstring priority on type present in param else on type
            "rst_type_in_param_priority": True,
        }
        self.special_signature_chars = ("/", "*")

        self.parse_definition()
        self.quotes = quotes

    def __str__(self) -> str:
        """Verbose, for debugging.

        Returns
        -------
        str
            String representation of DocString class.
        """
        txt = "\n\n** " + str(self.element["name"])
        txt += " of type " + str(self.element["deftype"]) + ":"
        txt += str(self.docs["in"]["desc"]) + "\n"
        txt += "->" + str(self.docs["in"]["params"]) + "\n"
        txt += "***>>" + str(self.docs["out"]["raw"]) + "\n" + "\n"
        return txt

    def __repr__(self) -> str:
        """Fall back to __str__.

        Returns
        -------
        str
            String representation of DocString class.
        """
        return self.__str__()

    def get_input_docstring(self) -> Optional[str]:
        """Get the input raw docstring.

        Returns
        -------
        Optional[str]
            the input docstring if any.
        """
        return self.docs["in"]["raw"]

    def get_input_style(self) -> str:
        """Get the input docstring style.

        Returns
        -------
        str
            the style for input docstring
        """
        # TODO: use a getter
        return self.dst.style

    def set_input_style(self, style: str) -> None:
        """Set input docstring style.

        Parameters
        ----------
        style : str
            style to set for input docstring
        """
        # TODO: use a setter
        self.dst.style = style

    def get_spaces(self) -> str:
        """Get the output docstring initial spaces.

        Returns
        -------
        str
            the spaces
        """
        return self.docs["out"]["spaces"]

    def set_spaces(self, spaces: str) -> None:
        """Set for output docstring the initial spaces.

        Parameters
        ----------
        spaces : str
            the spaces to set
        """
        self.docs["out"]["spaces"] = spaces

    def with_space(self, string: str, spaces: str) -> str:
        """Pad lines in string with spaces.

        Parameters
        ----------
        string : str
            String to pad with spaces.
        spaces : str
            Local spaces to add.

        Returns
        -------
        str
            Padded string
        """
        return "\n".join(
            [
                self.docs["out"]["spaces"] + spaces + line.lstrip()
                if i > 0 and line
                else line
                for i, line in enumerate(string.splitlines())
            ]
        )

    def parse_definition(self, raw: Optional[str] = None) -> None:
        """Parse the element's elements (type, name and parameters).

        e.g.: def methode(param1, param2='default')
        def                      -> type
        methode                  -> name
        param1, param2='default' -> parameters.

        Parameters
        ----------
        raw : Optional[str]
            raw data of the element (def or class).
            If None will use `self.element['raw']` (Default value = None)
        """
        # TODO: retrieve return from element external code (in parameter)
        line = self.element["raw"].strip() if raw is None else raw.strip()
        is_class = False
        if line.startswith(("async def ", "def ", "class ")):
            # retrieves the type
            if line.startswith("def"):
                self.element["deftype"] = "def"
                line = line.replace("def ", "")
            elif line.startswith("async"):
                self.element["deftype"] = "def"
                line = line.replace("async def ", "")
            else:
                self.element["deftype"] = "class"
                line = line.replace("class ", "")
                is_class = True
            # retrieves the name
            self.element["name"] = line[: line.find("(")].strip()
            if not is_class:
                self._parse_function_definition(line)
        self.parsed_elem = True

    # TODO Rename this here and in `parse_definition`
    def _parse_function_definition(self, line: str) -> None:
        """Parse the element's elements (type, name and parameters).

        e.g.: def methode(param1, param2='default')
        def                      -> type
        methode                  -> name
        param1, param2='default' -> parameters.

        Parameters
        ----------
        raw : Optional[str]
            raw data of the element (def or class).
            If None will use `self.element['raw']` (Default value = None)
        """
        extracted = self._extract_signature_elements(
            self._remove_signature_comment(line)
        )
        remove_keys = [
            key
            for key in extracted["parameters"]
            if extracted["parameters"][key]["param"] in ["self", "cls", ""]
        ]
        for key in remove_keys:
            del extracted["parameters"][key]
        if extracted["return_type"]:
            self.element["rtype"] = extracted["return_type"]  # TODO manage this
        self.element["params"].extend(extracted["parameters"].values())

    def _remove_signature_comment(self, txt: str) -> str:
        """If there is a comment at the end of the signature statement, remove it.

        Parameters
        ----------
        txt : str
            Signature line

        Returns
        -------
        str
            Cleaned signature line
        """
        ret = ""
        # This should be a list like in _extract_signature_elements
        # Otherwise in a situation like (((() the one closing parenthesis would
        # break us out of everything
        inside = None
        end_inside = {"(": ")", "{": "}", "[": "]", "'": "'", '"': '"'}
        for char in txt:
            if (inside and end_inside[inside] != char) or (
                not inside and char in end_inside
            ):
                if not inside:
                    inside = char
                ret += char
                continue
            if inside and char == end_inside[inside]:
                inside = None
                ret += char
                continue
            if not inside and char == "#":
                # found a comment so signature is finished we stop parsing
                break
            ret += char
        return ret

    def _extract_signature_elements(  # noqa: PLR0912, PLR0915
        self, txt: str
    ) -> Signatures:
        """Extract the signature elements from the function definition.

        foo(x: int, y: int, /, *, a: int, b: int) -> None:

        Parameters
        ----------
        txt : str
            Function signature string

        Returns
        -------
        Signatures
            Extracted elements
            {"parameters": elems, "return_type": return_type.strip()}
            Where elems is dict[int, dict[str, str]]:
            elems[elem_idx] = {"type": "", "param": "", "default": ""}
        """
        start = txt.find("(") + 1
        end_start = txt.rfind(")")
        end_end = txt.rfind(":")
        return_type = txt[end_start + 1 : end_end].replace("->", "").strip()
        elem_idx = 0
        # Make this an enum: TODO
        reading = "param"
        elems: Dict[int, Params] = {elem_idx: {"type": "", "param": "", "default": ""}}
        inside: list[str] = []  # Represents the bracket type we are in
        end_inside = {"(": ")", "{": "}", "[": "]", "'": "'", '"': '"'}
        for char in txt[start:end_start]:
            # We are in a block and we are not ending that block
            # or we are not in a block and we are starting a block
            if inside or (char in end_inside):
                # We are in the second condition and thus starting a block
                if char in end_inside:
                    inside.append(char)
                # Pretty sure something is broken here with quotes
                # They get added in the lines above and then instantly removed
                if char == end_inside[inside[-1]]:
                    inside.pop()
                # We are in the first block
                # If we are reading the type then the current char is appended
                if reading == "type":
                    elems[elem_idx]["type"] += char
                # If we are reading the default then append the char there
                elif reading == "default":
                    elems[elem_idx]["default"] += char
                else:
                    # FIXME: this should not happen!
                    msg = (
                        "unexpected nested element "
                        f"after {inside} while reading {reading}"
                    )
                    raise ValueError(msg)
                continue
            # We are currently reading a parameter (name?)
            if reading == "param":
                # We are not at a delimiter
                # So add it to the param name
                if char not in ": ,=":
                    elems[elem_idx]["param"] += char
                # We are at a delimiter
                # If we are at a space and our current param is empty or we are
                # not at a space then we are finished with the param
                elif char == " " and elems[elem_idx]["param"] or char != " ":
                    reading = "after_param"
            # If we are reading the type
            elif reading == "type":
                # If we are not reading , or = we are adding to our type
                if char not in ",=":
                    elems[elem_idx]["type"] += char
                # We are reading , or = and finished our type
                else:
                    reading = "after_type"
            elif reading == "default":
                if char != ",":
                    elems[elem_idx]["default"] += char
                else:
                    reading = "after_default"
            # If we are after param then ':' indicates now comes the type
            if reading.startswith("after_"):
                if reading == "after_param" and char == ":":
                    reading = "type"
                # Otherwise ',' indicates a new parameter
                elif char == ",":
                    elem_idx += 1
                    elems[elem_idx] = {"type": "", "param": "", "default": ""}
                    reading = "param"
                # and '=' indicates a default value
                elif char == "=":
                    reading = "default"
        # strip extracted elements
        # and iterate over a copy so we can delete elements that are just
        # "*" or "/" as those do not belong in the doctring.
        for elem in dict(elems):
            if elems[elem]["param"] in self.special_signature_chars:
                del elems[elem]
                continue
            for subelem in elems[elem]:
                elems[elem][subelem] = elems[elem][subelem].strip()
        return {"parameters": elems, "return_type": return_type.strip()}

    def _extract_docs_doctest(self) -> bool:
        """Extract the doctests if found.

        If there are doctests, they are removed from the input data and set on
        a specific buffer as they won't be altered.

        Returns
        -------
        bool
            True if found and proceeded else False
        """
        result = False
        data = self.docs["in"]["raw"]
        start, end = self.dst.get_doctests_indexes(data)
        while start != -1:
            result = True
            datalst = data.splitlines()
            if self.docs["in"]["doctests"] != "":
                self.docs["in"]["doctests"] += "\n"
            self.docs["in"]["doctests"] += "\n".join(datalst[start : end + 1]) + "\n"
            self.docs["in"]["raw"] = "\n".join(datalst[:start] + datalst[end + 1 :])
            data = self.docs["in"]["raw"]
            start, end = self.dst.get_doctests_indexes(data)
        if self.docs["in"]["doctests"] != "":
            data = "\n".join(
                [
                    d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                    for d in self.docs["in"]["doctests"].splitlines()
                ]
            )
            self.docs["out"]["doctests"] = data
        return result

    def _extract_docs_description(self) -> None:
        """Extract main description from docstring."""
        # FIXME: the indentation of descriptions is lost
        data = "\n".join(
            [
                d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                for d in self.docs["in"]["raw"].splitlines()
            ]
        )
        # TODO: use match?
        if self.dst.style == "groups":
            idx = self.dst.get_group_index(data)
        elif self.dst.style == "google":
            lines = data.splitlines()
            line_num = self.dst.googledoc.get_next_section_start_line(lines)
            idx = -1 if line_num == -1 else len("\n".join(lines[:line_num]))
        elif self.dst.style == "numpydoc":
            lines = data.splitlines()
            line_num = self.dst.numpydoc.get_next_section_start_line(lines)
            idx = -1 if line_num == -1 else len("\n".join(lines[:line_num]))
        elif self.dst.style == "unknown":
            idx = -1
        else:
            idx = self.dst.get_elem_index(data)
        if idx == 0:
            self.docs["in"]["desc"] = ""
        elif idx == -1:
            self.docs["in"]["desc"] = data
        else:
            self.docs["in"]["desc"] = data[:idx]

    def _extract_groupstyle_docs_params(self) -> None:
        """Extract group style parameters."""
        data = "\n".join(
            [
                d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                for d in self.docs["in"]["raw"].splitlines()
            ]
        )
        idx = self.dst.get_group_key_line(data, "param")
        if idx >= 0:
            data = data.splitlines()[idx + 1 :]
            end = self.dst.get_group_line("\n".join(data))
            end = end if end != -1 else len(data)
            ptype = ""
            for i in range(end):
                # FIXME: see how retrieve multiline param description and how get type
                line = data[i]
                param = None
                desc = ""
                if matches := re.match(r"^\W*(\w+)[\W\s]+(\w[\s\w]+)", line.strip()):
                    param = matches[1].strip()
                    desc = matches[2].strip()
                elif matches := re.match(r"^\W*(\w+)\W*", line.strip()):
                    param = matches[1].strip()
                if param:
                    self.docs["in"]["params"].append((param, desc, ptype))

    def _extract_tagstyle_docs_params(self) -> None:
        """Extract tagstyle parameters."""
        data = "\n".join(
            [
                d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                for d in self.docs["in"]["raw"].splitlines()
            ]
        )
        extracted = self.dst.extract_elements(data)
        for param_name, param in extracted.items():
            param_type = param["type"]
            if self._options["rst_type_in_param_priority"] and param["type_in_param"]:
                param_type = param["type_in_param"]
            desc = param["description"] or ""
            self.docs["in"]["params"].append((param_name, desc, param_type))

    def _old_extract_tagstyle_docs_params(self) -> None:
        """Extract tagstlye parameters manually, the old way."""
        data = "\n".join(
            [
                d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                for d in self.docs["in"]["raw"].splitlines()
            ]
        )
        listed = 0
        loop = True
        maxi = 10000  # avoid infinite loop but should never happen
        i = 0
        while loop:
            i += 1
            if i > maxi:
                loop = False
            start, end = self.dst.get_param_indexes(data)
            if start >= 0:
                param = data[start:end]
                desc = ""
                param_end = end
                start, end = self.dst.get_param_description_indexes(data, prev=end)
                if start > 0:
                    desc = data[start:end].strip()
                if end == -1:
                    end = param_end
                ptype = ""
                start, pend = self.dst.get_param_type_indexes(
                    data, name=param, prev=end
                )
                if start > 0:
                    ptype = data[start:pend].strip()
                # a parameter is stored with: (name, description, type)
                self.docs["in"]["params"].append((param, desc, ptype))
                data = data[end:]
                listed += 1
            else:
                loop = False
        if i > maxi:
            print(
                "WARNING: an infinite loop was reached while extracting "
                "docstring parameters (>10000). This should never happen!!!"
            )

    def _extract_docs_params(self) -> None:
        """Extract parameters description and type from docstring.

        The internal computed parameters list is
        composed by tuples (parameter, description, type).
        """
        if self.dst.style == "numpydoc":
            data = "\n".join(
                [
                    d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                    for d in self.docs["in"]["raw"].splitlines()
                ]
            )
            self.docs["in"]["params"] += self.dst.numpydoc.get_param_list(data)
        elif self.dst.style == "google":
            data = "\n".join(
                [
                    d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                    for d in self.docs["in"]["raw"].splitlines()
                ]
            )
            self.docs["in"]["params"] += self.dst.googledoc.get_param_list(data)
        elif self.dst.style == "groups":
            self._extract_groupstyle_docs_params()
        elif self.dst.style in ["javadoc", "reST"]:
            self._extract_tagstyle_docs_params()

    def _extract_groupstyle_docs_raises(self) -> None:
        """Extract raises section from group style docstrings."""
        data = "\n".join(
            [
                d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                for d in self.docs["in"]["raw"].splitlines()
            ]
        )
        idx = self.dst.get_group_key_line(data, "raise")
        if idx >= 0:
            data = data.splitlines()[idx + 1 :]
            end = self.dst.get_group_line("\n".join(data))
            end = end if end != -1 else len(data)
            for i in range(end):
                # FIXME: see how retrieve multiline raise description
                line = data[i]
                param = None
                desc = ""
                if matches := re.match(r"^\W*([\w.]+)[\W\s]+(\w[\s\w]+)", line.strip()):
                    param = matches[1].strip()
                    desc = matches[2].strip()
                elif matches := re.match(r"^\W*(\w+)\W*", line.strip()):
                    param = matches[1].strip()
                if param:
                    self.docs["in"]["raises"].append((param, desc))

    def _extract_tagstyle_docs_raises(self) -> None:
        """Extract raises section from tagstyle docstrings."""
        data = "\n".join(
            [
                d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                for d in self.docs["in"]["raw"].splitlines()
            ]
        )
        listed = 0
        loop = True
        maxi = 10000  # avoid infinite loop but should never happen
        i = 0
        while loop:
            i += 1
            if i > maxi:
                loop = False
            start, end = self.dst.get_raise_indexes(data)
            if start >= 0:
                param = data[start:end]
                desc = ""
                start, end = self.dst.get_raise_description_indexes(data, prev=end)
                if start > 0:
                    desc = data[start:end].strip()
                # a parameter is stored with: (name, description)
                self.docs["in"]["raises"].append((param, desc))
                data = data[end:]
                listed += 1
            else:
                loop = False
        if i > maxi:
            print(
                "WARNING: an infinite loop was reached while extracting "
                "docstring parameters (>10000). This should never happen!!!"
            )

    def _extract_docs_raises(self) -> None:
        """Extract raises description from docstring.

        The internal computed raises list is composed by tuples (raise, description).
        """
        if self.dst.style == "numpydoc":
            data = "\n".join(
                [
                    d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                    for d in self.docs["in"]["raw"].splitlines()
                ]
            )
            self.docs["in"]["raises"] += self.dst.numpydoc.get_raise_list(data)
        if self.dst.style == "google":
            data = "\n".join(
                [
                    d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                    for d in self.docs["in"]["raw"].splitlines()
                ]
            )
            self.docs["in"]["raises"] += self.dst.googledoc.get_raise_list(data)
        elif self.dst.style == "groups":
            self._extract_groupstyle_docs_raises()
        elif self.dst.style in ["javadoc", "reST"]:
            self._extract_tagstyle_docs_raises()

    def _extract_groupstyle_docs_return(self) -> None:
        """Extract return section from groupstyle docstrings."""
        # TODO: manage rtype
        data = "\n".join(
            [
                d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                for d in self.docs["in"]["raw"].splitlines()
            ]
        )
        idx = self.dst.get_group_key_line(data, "return")
        if idx >= 0:
            data = data.splitlines()[idx + 1 :]
            end = self.dst.get_group_line("\n".join(data))
            end = end if end != -1 else len(data)
            data = "\n".join(data[:end]).strip()
            self.docs["in"]["return"] = data.rstrip()

    def _extract_tagstyle_docs_return(self) -> None:
        """Extract return section from tagstyle docstrings."""
        data = "\n".join(
            [
                d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                for d in self.docs["in"]["raw"].splitlines()
            ]
        )
        start, end = self.dst.get_return_description_indexes(data)
        if start >= 0:
            if end >= 0:
                self.docs["in"]["return"] = data[start:end].rstrip()
            else:
                self.docs["in"]["return"] = data[start:].rstrip()
        start, end = self.dst.get_return_type_indexes(data)
        if start >= 0:
            if end >= 0:
                self.docs["in"]["rtype"] = data[start:end].rstrip()
            else:
                self.docs["in"]["rtype"] = data[start:].rstrip()

    def _extract_docs_return(self) -> None:
        """Extract return description and type."""
        if self.dst.style == "numpydoc":
            data = "\n".join(
                [
                    d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                    for d in self.docs["in"]["raw"].splitlines()
                ]
            )
            self.docs["in"]["return"] = self.dst.numpydoc.get_return_list(data)
            self.docs["in"]["rtype"] = None
        # TODO: fix this
        elif self.dst.style == "google":
            data = "\n".join(
                [
                    d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                    for d in self.docs["in"]["raw"].splitlines()
                ]
            )
            self.docs["in"]["return"] = self.dst.googledoc.get_return_list(data)
            self.docs["in"]["rtype"] = None
        elif self.dst.style == "groups":
            self._extract_groupstyle_docs_return()
        elif self.dst.style in ["javadoc", "reST"]:
            self._extract_tagstyle_docs_return()

    def _extract_docs_other(self) -> None:
        """Extract other specific sections."""
        if self.dst.style == "numpydoc":
            data = "\n".join(
                [
                    d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                    for d in self.docs["in"]["raw"].splitlines()
                ]
            )
            self.dst.numpydoc.get_list_key(data, "also")
            self.dst.numpydoc.get_list_key(data, "ref")
            self.dst.numpydoc.get_list_key(data, "note")
            self.dst.numpydoc.get_list_key(data, "other")
            self.dst.numpydoc.get_list_key(data, "example")
            self.dst.numpydoc.get_list_key(data, "attr")
            # TODO do something with this?

    def parse_docs(self, raw: Optional[str] = None, before_lim: str = "") -> None:
        """Parse the docstring.

        Parameters
        ----------
        raw : Optional[str]
            the data to parse if not internally provided (Default value = None)
        before_lim : str
            specify raw or unicode or format docstring type
            (ie. "r" for r'''... or "fu" for fu'''...) (Default value = "")
        """
        self.before_lim = before_lim
        if raw is not None:
            self._clean_and_set_raw(raw)
        if not self.docs["in"]["raw"]:
            return
        self.dst.set_known_parameters(self.element["params"])
        self._extract_docs_doctest()
        self._extract_docs_params()
        self._extract_docs_return()
        self._extract_docs_raises()
        self._extract_docs_description()
        self._extract_docs_other()
        self.parsed_docs = True

    def _clean_and_set_raw(self, raw: str) -> None:
        """Clean raw string and set raw input sections.

        Also call autodetect_style.
        """
        raw = raw.strip()
        if raw.startswith(('"""', "'''")):
            raw = raw[3:]
        if raw.endswith(('"""', "'''")):
            raw = raw[:-3]
        self.docs["in"]["raw"] = raw
        self.docs["in"]["pure_raw"] = raw
        self.dst.autodetect_style(raw)

    def _set_desc(self) -> None:
        """Set the global description if any."""
        # TODO: manage different in/out styles
        self.docs["out"]["desc"] = self.docs["in"]["desc"] or ""

    def _set_params(self) -> None:
        """Set the parameters with types, descriptions and default value if any.

        Taken from the input docstring and the signature parameters.
        """
        # TODO: manage different in/out styles
        # convert the list of signature's extracted params
        # into a dict with the names of param as keys
        sig_params = {
            e["param"]: {"type": e["type"], "default": e["default"]}
            for e in self.element["params"]
        }
        # convert the list of docsting's extracted params
        # into a dict with the names of param as keys
        docs_params = {
            name: {
                "description": desc,
                "type": param_type,
            }
            for name, desc, param_type in self.docs["in"]["params"]
        }
        for name in sig_params:
            # WARNING: Note that if a param in docstring isn't in the signature params,
            # it will be dropped
            sig_type, sig_default = (
                sig_params[name]["type"],
                sig_params[name]["default"],
            )
            out_description = ""
            out_type = sig_type or None
            out_default = sig_default or None
            if name in docs_params:
                out_description = docs_params[name]["description"]
                if not out_type or (
                    not self._options["hint_type_priority"]
                    and docs_params[name]["type"]
                ):
                    out_type = docs_params[name]["type"]
            self.docs["out"]["params"].append(
                (name, out_description, out_type, out_default)
            )

    def _set_raises(self) -> None:
        """Set the raises and descriptions."""
        # TODO: manage different in/out styles
        # manage setting if not mandatory for numpy but optional
        # list of parameters is like: (name, description)
        self.docs["out"]["raises"] = list(self.docs["in"]["raises"])

    def _set_return(self) -> None:
        """Set return parameter with description and rtype if any."""
        # TODO: manage return retrieved from element code (external)
        # TODO: manage different in/out styles
        self.docs["out"]["return"] = self.docs["in"]["return"]
        self.docs["out"]["rtype"] = self.docs["in"]["rtype"]
        if (
            self._options["hint_rtype_priority"] or not self.docs["out"]["rtype"]
        ) and self.element["rtype"]:
            self.docs["out"]["rtype"] = self.element["rtype"]

    def _set_other(self) -> None:
        """Set other specific sections."""
        # manage not setting if not mandatory for numpy
        if self.dst.style == "numpydoc":
            if self.docs["in"]["raw"]:
                self.docs["out"]["post"] = self.dst.numpydoc.get_raw_not_managed(
                    self.docs["in"]["raw"]
                )
            elif "post" not in self.docs["out"] or self.docs["out"]["post"] is None:
                self.docs["out"]["post"] = ""

    def _set_raw_params(self, _sep: str) -> None:
        """Set the output raw parameters section.

        Parameters
        ----------
        sep : str
            the separator of current style
        """
        if not self.docs["out"]["params"]:
            return ""
        raw = "\n\n"
        spaces = " " * 4

        raw += self.dst.numpydoc.get_key_section_header(
            "param", self.docs["out"]["spaces"]
        )
        for i, param in enumerate(self.docs["out"]["params"]):
            raw += self.docs["out"]["spaces"] + param[0] + " :"
            if param[2] is not None and len(param[2]) > 0:
                raw += f" {param[2]}"
            else:
                raw += " _type_"
            raw += "\n"
            description = (
                spaces + self.with_space(param[1] or "_description_", spaces).strip()
            )
            raw += self.docs["out"]["spaces"] + description
            # Where does the 4th element come from?
            # I guess like name, description, type, default?

            if "default" not in param[1].lower() and param[3] is not None:
                raw += (
                    " (Default value = " + str(param[3]) + ")"
                    if description
                    else (
                        self.docs["out"]["spaces"] * 2
                        + "(Default value = "
                        + str(param[3])
                        + ")"
                    )
                )
            if i != len(self.docs["out"]["params"]) - 1:
                raw += "\n"

        return raw

    def _set_raw_raise(self, _sep: str) -> None:
        """Set the output raw exception section.

        Parameters
        ----------
        sep : str
            the separator of current style
        """
        raw = ""
        if "raise" not in self.dst.numpydoc.get_excluded_sections() and (
            "raise" in self.dst.numpydoc.get_mandatory_sections()
            or (
                self.docs["out"]["raises"]
                and "raise" in self.dst.numpydoc.get_optional_sections()
            )
        ):
            raw += "\n\n"
            raw += self.dst.numpydoc.get_key_section_header(
                "raise", self.docs["out"]["spaces"]
            )
            if self.docs["out"]["raises"]:
                spaces = " " * 4

                for i, entry in enumerate(self.docs["out"]["raises"]):
                    raw += self.docs["out"]["spaces"] + entry[0] + "\n"
                    raw += (
                        self.docs["out"]["spaces"]
                        + spaces
                        + self.with_space(entry[1], spaces).strip()
                    )
                    if i != len(self.docs["out"]["raises"]) - 1:
                        raw += "\n"
        return raw

    def _none_return(self, return_value: Optional[str]) -> bool:
        """Check if the return type was not set or set as None.

        Parameters
        ----------
        return_value : Optional[str]
            Read return type

        Returns
        -------
        bool
            _description_
        """
        return return_value is None or return_value == "None"

    def _set_raw_return(self, _sep: str) -> None:
        """Set the output raw return section.

        Parameters
        ----------
        sep : str
            the separator of current style
        """
        raw = ""
        returned_values = self.docs["out"]["return"]
        # If there is a docstring but no return section
        # Then do not create one just to specify it as none
        if (
            self.docs["in"]["raw"]
            and not self.docs["in"]["return"]
            and self._none_return(self.docs["out"]["rtype"])
        ):
            return raw
        raw += "\n\n"
        spaces = " " * 4

        raw += self.dst.numpydoc.get_key_section_header(
            "return", self.docs["out"]["spaces"]
        )
        rtype = self.docs["out"]["rtype"]
        type_placeholder = "_type_"
        # case of several returns
        # Here an existing docstring takes precedence over the type hint.
        # As the type hint could just be tuple[A, B, C] but the docstring
        # Could already be specifying each entry individually.
        if isinstance(returned_values, list) and len(returned_values) > 1:
            for i, ret_elem in enumerate(returned_values):
                # if tuple (name, desc, rtype) else string desc
                rtype = ret_elem[2] or type_placeholder
                raw += self.docs["out"]["spaces"]
                if ret_elem[0]:
                    raw += f"{ret_elem[0]} : "
                if ret_elem[1]:
                    raw += (
                        rtype
                        + "\n"
                        + self.docs["out"]["spaces"]
                        + spaces
                        + self.with_space(ret_elem[1], spaces).strip()
                    )
                if i != len(returned_values) - 1:
                    raw += "\n"

        # case of a unique return
        # Length exactly 1
        # Here the type hint has precedence again
        elif isinstance(returned_values, list) and returned_values:
            ret_elem = returned_values[0]  # pylint: disable=unsubscriptable-object
            rtype = rtype or ret_elem[2] or type_placeholder
            raw += self.docs["out"]["spaces"]
            if ret_elem[0]:
                raw += f"{ret_elem[0]} : "
            if ret_elem[1]:
                raw += (
                    rtype
                    + "\n"
                    + self.docs["out"]["spaces"]
                    + spaces
                    + self.with_space(ret_elem[1], spaces).strip()
                )
        # Just a string, usually when the section is missing completely.
        else:
            rtype = rtype or type_placeholder
            raw += self.docs["out"]["spaces"] + rtype
            raw += (
                "\n"
                + self.docs["out"]["spaces"]
                + spaces
                + self.with_space(
                    returned_values or "_description_",
                    spaces,
                ).strip()
            )
        return raw

    def _set_raw(self) -> None:
        """Set the output raw docstring."""
        sep = self.dst.get_sep(target="out")
        sep = f"{sep} " if sep != " " else sep

        # sets the description section
        raw = self.docs["out"]["spaces"] + self.before_lim + self.quotes
        lines = self.docs["out"]["desc"].splitlines()
        # Add a period to the first line if not present
        if lines and lines[0] and not lines[0].endswith("."):
            lines[0] += "."
        desc = self.docs["out"]["desc"].strip()

        self.docs["out"]["desc"] = "\n".join(lines)
        raw += self.with_space(
            self.docs["out"]["desc"] if desc else "_summary_.", ""
        ).strip()

        # sets the parameters section
        raw += self._set_raw_params(sep)

        # sets the return section
        raw += self._set_raw_return(sep)

        # sets the raises section
        raw += self._set_raw_raise(sep)

        # sets post specific if any
        if (
            "post" in self.docs["out"]
            and self.with_space(self.docs["out"]["post"], "").rstrip()
        ):
            raw += self.with_space(self.docs["out"]["post"], "").rstrip()

        # sets the doctests if any
        if "doctests" in self.docs["out"]:
            raw += (
                "\n"
                + self.docs["out"]["spaces"]
                + self.with_space(self.docs["out"]["doctests"], "").strip()
            )

        if raw.count(self.quotes) == 1:
            if raw.count("\n") > 0:
                raw += "\n" + self.docs["out"]["spaces"]
            raw += self.quotes

        self.docs["out"]["raw"] = raw.rstrip()

    def generate_docs(self) -> None:
        """Generate the output docstring."""
        self._set_desc()
        self._set_params()
        self._set_return()
        self._set_raises()
        self._set_other()
        self._set_raw()
        self.generated_docs = True

    def get_raw_docs(self) -> str:
        """Generate raw docstring.

        Returns
        -------
        _type_
            the raw docstring
        """
        if not self.generated_docs:
            self.generate_docs()
        return self.docs["out"]["raw"]


if __name__ == "__main__":
    help(DocString)
