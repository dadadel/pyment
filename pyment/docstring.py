"""Module for actually parsing and producing docstrings."""
import re
from typing import Optional

from .docstringssssss.parsers import Docs, DocsTools

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


class DocString:
    """This class represents the docstring."""

    def __init__(  # noqa: PLR0913
        self,
        elem_raw: str,
        spaces: str = "",
        docs_raw: Optional[str] = None,
        quotes: str = "'''",
        input_style: Optional[str] = None,
        *,
        type_stub: bool = False,
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
        type_stub : bool
            if set, an empty stub will be created for a parameter type (Default value = False)
        before_lim : str
            specify raw or unicode or format docstring type (ie. "r" for r'''... or "fu" for fu'''...) (Default value = "")
        indent : int
            _description_ (Default value = 2)
        """
        self.dst = DocsTools()
        self.before_lim = before_lim
        self.type_stub = type_stub
        if docs_raw and not input_style:
            self.dst.autodetect_style(docs_raw)
        elif input_style:
            self.set_input_style(input_style)
        self.element = {
            "raw": elem_raw,
            "name": None,
            "type": None,
            "params": [],
            "spaces": spaces,
            "rtype": None,
        }
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
        elif (len(spaces) % 4) == 0 or spaces == "":
            # FIXME: should bug if tabs for class or function (as spaces=='')
            self.docs["out"]["spaces"] = spaces + " " * 4
        self.parsed_elem = False
        self.parsed_docs = False
        self.generated_docs = False
        self._options = {
            "hint_rtype_priority": True,  # priority in type hint else in docstring
            "hint_type_priority": True,  # priority in type hint else in docstring
            "rst_type_in_param_priority": True,  # in reST docstring priority on type present in param else on type
        }
        self.special_signature_chars = ("/", "*")

        self.parse_definition()
        self.quotes = quotes

    def __str__(self) -> str:
        """Verbose, for debugging.

        Returns
        -------
        str
            _description_
        """
        # for debuging
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
            _description_
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

    def set_input_style(self, style: str):
        """Sets the input docstring style.

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

    def set_spaces(self, spaces: str):
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

    def parse_definition(self, raw: Optional[str] = None):
        """Parses the element's elements (type, name and parameters) :).
        e.g.: def methode(param1, param2='default')
        def                      -> type
        methode                  -> name
        param1, param2='default' -> parameters.

        Parameters
        ----------
        raw : Optional[str]
            raw data of the element (def or class). If None will use `self.element['raw']` (Default value = None)
        """
        # TODO: retrieve return from element external code (in parameter)
        l = self.element["raw"].strip() if raw is None else raw.strip()
        is_class = False
        if l.startswith(("async def ", "def ", "class ")):
            # retrieves the type
            if l.startswith("def"):
                self.element["deftype"] = "def"
                l = l.replace("def ", "")
            elif l.startswith("async"):
                self.element["deftype"] = "def"
                l = l.replace("async def ", "")
            else:
                self.element["deftype"] = "class"
                l = l.replace("class ", "")
                is_class = True
            # retrieves the name
            self.element["name"] = l[: l.find("(")].strip()
            if not is_class:
                extracted = self._extract_signature_elements(
                    self._remove_signature_comment(l)
                )
                # remove self and cls parameters if any and also empty params (if no param)
                remove_keys = []
                for key in extracted["parameters"]:
                    if extracted["parameters"][key]["param"] in ["self", "cls"]:
                        remove_keys.append(key)
                    elif not extracted["parameters"][key]["param"]:
                        remove_keys.append(key)
                for key in remove_keys:
                    del extracted["parameters"][key]
                if extracted["return_type"]:
                    self.element["rtype"] = extracted["return_type"]  # TODO manage this
                self.element["params"].extend(extracted["parameters"].values())
        self.parsed_elem = True

    def _remove_signature_comment(self, txt: str) -> str:
        """If there is a comment at the end of the signature statement, remove it.

        Parameters
        ----------
        txt : str
            _description_

        Returns
        -------
        str
            _description_
        """
        ret = ""
        inside = None
        end_inside = {"(": ")", "{": "}", "[": "]", "'": "'", '"': '"'}
        for c in txt:
            if (inside and end_inside[inside] != c) or (not inside and c in end_inside):
                if not inside:
                    inside = c
                ret += c
                continue
            if inside and c == end_inside[inside]:
                inside = None
                ret += c
                continue
            if not inside and c == "#":
                # found a comment so signature is finished we stop parsing
                break
            ret += c
        return ret

    def _extract_signature_elements(self, txt: str) -> dict:
        """Extract the signature elements from the function definition.

        foo(x: int, y: int, /, *, a: int, b: int) -> None:

        Parameters
        ----------
        txt : str
            Function signature string

        Returns
        -------
        dict
            Extracted elements
            {"parameters": elems, "return_type": return_type.strip()}
            Where elems is dict[int, dict[str, str]]:
            elems[elem_idx] = {"type": "", "param": "", "default": ""}
        """
        start = txt.find("(") + 1
        end_start = txt.rfind(")")
        end_end = txt.rfind(":")
        return_type = txt[end_start + 1 : end_end].replace("->", "").strip()
        elems = {}
        elem_idx = 0
        reading = "param"
        elems[elem_idx] = {"type": "", "param": "", "default": ""}
        inside: list[str] = []  # Represents the bracket type we are in
        end_inside = {"(": ")", "{": "}", "[": "]", "'": "'", '"': '"'}
        for c in txt[start:end_start]:
            # We are in a block and we are not ending that block
            # or we are not in a block and we are starting a block
            if (inside) or (c in end_inside):
                # We are in the second condition and thus starting a block
                if c in end_inside:
                    inside.append(c)
                if c == end_inside[inside[-1]]:
                    inside.pop()
                # We are in the first block
                # If we are reading the type then the current char is appended
                if reading == "type":
                    elems[elem_idx]["type"] += c
                # If we are reading the default then append the char there
                elif reading == "default":
                    elems[elem_idx]["default"] += c
                else:
                    # FIXME: this should not happen!
                    raise Exception(
                        "unexpected nested element after "
                        + str(inside)
                        + " while reading "
                        + reading
                    )
                continue
            # We are currently reading a parameter (name?)
            if reading == "param":
                # We are not at a delimiter
                # So add it to the param name
                if c not in ": ,=":
                    elems[elem_idx]["param"] += c
                # We are at a delimiter
                else:
                    # If we are at a space and our current param is empty or we are
                    # not at a space then we are finished with the param
                    if c == " " and elems[elem_idx]["param"] or c != " ":
                        reading = "after_param"
            # If we are reading the type
            elif reading == "type":
                # If we are not reading , or = we are adding to our type
                if c not in ",=":
                    elems[elem_idx]["type"] += c
                # We are reading , or = and finished our type
                else:
                    reading = "after_type"
            elif reading == "default":
                if c != ",":
                    elems[elem_idx]["default"] += c
                else:
                    reading = "after_default"
            # If we are after param then ':' indicates now comes the type
            if reading.startswith("after_"):
                if reading == "after_param" and c == ":":
                    reading = "type"
                # Otherwise ',' indicates a new parameter
                elif c == ",":
                    elem_idx += 1
                    elems[elem_idx] = {"type": "", "param": "", "default": ""}
                    reading = "param"
                # and '=' indicates a default value
                elif c == "=":
                    reading = "default"
        # strip extracted elements
        # and iterate over a copy so we can delete elements that are just
        # "*" or "/" as those do not belong in the doctring.
        for elem in dict(elems):
            if elems[elem]["param"] in self.special_signature_chars:
                del elems[elem]
                continue
            for subelem in elems[elem]:
                if type(elems[elem][subelem]) is str:
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
            for i in range(end):
                # FIXME: see how retrieve multiline param description and how get type
                line = data[i]
                param = None
                desc = ""
                ptype = ""
                m = re.match(r"^\W*(\w+)[\W\s]+(\w[\s\w]+)", line.strip())
                if m:
                    param = m.group(1).strip()
                    desc = m.group(2).strip()
                else:
                    m = re.match(r"^\W*(\w+)\W*", line.strip())
                    if m:
                        param = m.group(1).strip()
                if param:
                    self.docs["in"]["params"].append((param, desc, ptype))

    def _extract_tagstyle_docs_params(self):
        """_summary_."""
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
            desc = param["description"] if param["description"] else ""
            self.docs["in"]["params"].append((param_name, desc, param_type))

    def _old_extract_tagstyle_docs_params(self):
        """_summary_."""
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
                "WARNING: an infinite loop was reached while extracting docstring parameters (>10000). This should never happen!!!"
            )

    def _extract_docs_params(self):
        """Extract parameters description and type from docstring. The internal computed parameters list is.
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

    def _extract_groupstyle_docs_raises(self):
        """_summary_."""
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
                m = re.match(r"^\W*([\w.]+)[\W\s]+(\w[\s\w]+)", line.strip())
                if m:
                    param = m.group(1).strip()
                    desc = m.group(2).strip()
                else:
                    m = re.match(r"^\W*(\w+)\W*", line.strip())
                    if m:
                        param = m.group(1).strip()
                if param:
                    self.docs["in"]["raises"].append((param, desc))

    def _extract_tagstyle_docs_raises(self):
        """_summary_."""
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
                "WARNING: an infinite loop was reached while extracting docstring parameters (>10000). This should never happen!!!"
            )

    def _extract_docs_raises(self):
        """Extract raises description from docstring. The internal computed raises list is.
        composed by tuples (raise, description).
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

    def _extract_groupstyle_docs_return(self):
        """_summary_."""
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

    def _extract_tagstyle_docs_return(self):
        """_summary_."""
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

    def _extract_docs_return(self):
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

    def _extract_docs_other(self):
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

    def parse_docs(self, raw: Optional[str] = None, before_lim: str = ""):
        """Parses the docstring.

        Parameters
        ----------
        raw : Optional[str]
            the data to parse if not internally provided (Default value = None)
        before_lim : str
            specify raw or unicode or format docstring type (ie. "r" for r'''... or "fu" for fu'''...) (Default value = "")
        """
        self.before_lim = before_lim
        if raw is not None:
            raw = raw.strip()
            if raw.startswith(('"""', "'''")):
                raw = raw[3:]
            if raw.endswith(('"""', "'''")):
                raw = raw[:-3]
            self.docs["in"]["raw"] = raw
            self.docs["in"]["pure_raw"] = raw
            self.dst.autodetect_style(raw)
        if self.docs["in"]["raw"] is None:
            return
        self.dst.set_known_parameters(self.element["params"])
        self._extract_docs_doctest()
        self._extract_docs_params()
        self._extract_docs_return()
        self._extract_docs_raises()
        self._extract_docs_description()
        self._extract_docs_other()
        self.parsed_docs = True

    def _set_desc(self):
        """Sets the global description if any."""
        # TODO: manage different in/out styles
        if self.docs["in"]["desc"]:
            self.docs["out"]["desc"] = self.docs["in"]["desc"]
        else:
            self.docs["out"]["desc"] = ""

    def _set_params(self):
        """Sets the parameters with types, descriptions and default value if any.
        taken from the input docstring and the signature parameters.
        """
        # TODO: manage different in/out styles
        # convert the list of signature's extracted params into a dict with the names of param as keys
        sig_params = {
            e["param"]: {"type": e["type"], "default": e["default"]}
            for e in self.element["params"]
        }
        # convert the list of docsting's extracted params into a dict with the names of param as keys
        docs_params = {
            name: {
                "description": desc,
                "type": param_type,
            }
            for name, desc, param_type in self.docs["in"]["params"]
        }
        for name in sig_params:
            # WARNING: Note that if a param in docstring isn't in the signature params, it will be dropped
            sig_type, sig_default = (
                sig_params[name]["type"],
                sig_params[name]["default"],
            )
            out_description = ""
            out_type = sig_type if sig_type else None
            out_default = sig_default if sig_default else None
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
            if self.docs["in"]["raw"] is not None:
                self.docs["out"]["post"] = self.dst.numpydoc.get_raw_not_managed(
                    self.docs["in"]["raw"]
                )
            elif "post" not in self.docs["out"] or self.docs["out"]["post"] is None:
                self.docs["out"]["post"] = ""

    def _set_raw_params(self, sep):
        """Set the output raw parameters section.

        Parameters
        ----------
        sep : _type_
            the separator of current style
        """
        if not self.docs["out"]["params"]:
            return ""
        raw = "\n\n"
        spaces = " " * 4

        raw += self.dst.numpydoc.get_key_section_header(
            "param", self.docs["out"]["spaces"]
        )
        for i, p in enumerate(self.docs["out"]["params"]):
            raw += self.docs["out"]["spaces"] + p[0] + " :"
            if p[2] is not None and len(p[2]) > 0:
                raw += " " + p[2]
            else:
                raw += " " + "_type_"
            raw += "\n"
            description = (
                spaces
                + self.with_space(p[1] if p[1] else "_description_", spaces).strip()
            )
            raw += self.docs["out"]["spaces"] + description
            if len(p) > 2 and (
                "default" not in p[1].lower() and len(p) > 3 and p[3] is not None
            ):
                raw += (
                    " (Default value = " + str(p[3]) + ")"
                    if description
                    else (
                        self.docs["out"]["spaces"] * 2
                        + "(Default value = "
                        + str(p[3])
                        + ")"
                    )
                )
            if i != len(self.docs["out"]["params"]) - 1:
                raw += "\n"

        return raw

    def _set_raw_raise(self, sep):
        """Set the output raw exception section.

        Parameters
        ----------
        sep : _type_
            the separator of current style
        """
        raw = ""
        if "raise" not in self.dst.numpydoc.get_excluded_sections():
            if "raise" in self.dst.numpydoc.get_mandatory_sections() or (
                self.docs["out"]["raises"]
                and "raise" in self.dst.numpydoc.get_optional_sections()
            ):
                raw += "\n\n"
                spaces = " " * 4

                raw += self.dst.numpydoc.get_key_section_header(
                    "raise", self.docs["out"]["spaces"]
                )
                if len(self.docs["out"]["raises"]):
                    for i, p in enumerate(self.docs["out"]["raises"]):
                        raw += self.docs["out"]["spaces"] + p[0] + "\n"
                        raw += (
                            self.docs["out"]["spaces"]
                            + spaces
                            + self.with_space(p[1], spaces).strip()
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

    def _set_raw_return(self, sep):
        """Set the output raw return section.

        Parameters
        ----------
        sep : _type_
            the separator of current style
        """
        raw = ""
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
        rtype = self.docs["out"]["rtype"] if self.docs["out"]["rtype"] else "_type_"
        # case of several returns
        # Here an existing docstring takes precedence over the type hint.
        # As the type hint could just be tuple[A, B, C] but the docstring
        # Could already be specifying each entry individually.
        if (
            isinstance(self.docs["out"]["return"], list)
            and len(self.docs["out"]["return"]) > 1
        ):
            for i, ret_elem in enumerate(self.docs["out"]["return"]):
                # if tuple (name, desc, rtype) else string desc
                if isinstance(ret_elem, tuple) and len(ret_elem) == 3:
                    rtype = ret_elem[2]
                    if rtype is None:
                        rtype = ""
                    raw += self.docs["out"]["spaces"]
                    if ret_elem[0]:
                        raw += ret_elem[0] + " : "
                    if ret_elem[1]:
                        raw += (
                            rtype
                            + "\n"
                            + self.docs["out"]["spaces"]
                            + spaces
                            + self.with_space(ret_elem[1], spaces).strip()
                        )
                    if i != len(self.docs["out"]["return"]) - 1:
                        raw += "\n"
                else:
                    # There can be a problem
                    raw += self.docs["out"]["spaces"] + rtype + "\n"
                    if ret_elem:
                        raw += (
                            self.docs["out"]["spaces"]
                            + spaces
                            + self.with_space(str(ret_elem), spaces).strip()
                        )

        # case of a unique return
        # Length exactly 1
        # Here the type hint has precedence again
        elif (
            isinstance(self.docs["out"]["return"], list) and self.docs["out"]["return"]
        ):
            ret_elem = self.docs["out"]["return"][0]
            if type(ret_elem) is tuple and len(ret_elem) == 3:
                rtype = ret_elem[2]
                if rtype is None:
                    rtype = ""
                raw += self.docs["out"]["spaces"]
                if ret_elem[0]:
                    raw += ret_elem[0] + " : "
                if ret_elem[1]:
                    raw += (
                        rtype
                        + "\n"
                        + self.docs["out"]["spaces"]
                        + spaces
                        + self.with_space(ret_elem[1], spaces).strip()
                    )
            else:
                # There can be a problem
                raw += self.docs["out"]["spaces"] + rtype + "\n"
                if ret_elem:
                    raw += (
                        self.docs["out"]["spaces"]
                        + spaces
                        + self.with_space(str(ret_elem), spaces).strip()
                    )
        else:
            raw += self.docs["out"]["spaces"] + rtype
            raw += (
                "\n"
                + self.docs["out"]["spaces"]
                + spaces
                + self.with_space(
                    self.docs["out"]["return"]
                    if self.docs["out"]["return"]
                    else "_description_",
                    spaces,
                ).strip()
            )
        return raw

    def _set_raw(self):
        """Sets the output raw docstring."""
        sep = self.dst.get_sep(target="out")
        sep = sep + " " if sep != " " else sep

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
