# -*- coding: utf-8 -*-

import re
from collections import defaultdict

from pyment.docs_tools import DocsTools
from pyment.utils import get_leading_spaces, isin, isin_alone, isin_start

__author__ = "A. Daouzli"
__copyright__ = "Copyright 2012-2018, A. Daouzli"
__licence__ = "GPL3"
__version__ = "0.3.3"
__maintainer__ = "A. Daouzli"

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
    """This class represents the docstring"""

    def __init__(
        self,
        elem_raw,
        spaces="",
        docs_raw=None,
        quotes="'''",
        input_style=None,
        output_style=None,
        first_line=False,
        trailing_space=True,
        type_stub=False,
        before_lim="",
        **kwargs,
    ):
        """
        :param elem_raw: raw data of the element (def or class).
        :param spaces: the leading whitespaces before the element
        :param docs_raw: the raw data of the docstring part if any.
        :param quotes: the type of quotes to use for output: ' ' ' or " " "
        :param style_in: docstring input style ('javadoc', 'reST', 'groups', 'numpydoc', 'google', None).
          If None will be autodetected
        :type style_in: string
        :param style_out: docstring output style ('javadoc', 'reST', 'groups', 'numpydoc', 'google')
        :type style_out: string
        :param first_line: indicate if description should start
          on first or second line
        :type first_line: boolean
        :param trailing_space: if set, a trailing space will be inserted in places where the user
          should write a description
        :type trailing_space: boolean
        :param type_stub: if set, an empty stub will be created for a parameter type
        :type type_stub: boolean
        :param before_lim: specify raw or unicode or format docstring type (ie. "r" for r'''... or "fu" for fu'''...)

        """
        self.dst = DocsTools()
        self.before_lim = before_lim
        self.first_line = first_line
        self.trailing_space = ""
        self.type_stub = type_stub
        if trailing_space:
            self.trailing_space = " "
        if docs_raw and not input_style:
            self.dst.autodetect_style(docs_raw)
        elif input_style:
            self.set_input_style(input_style)
        if output_style:
            self.set_output_style(output_style)
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
            if docs_raw.startswith('"""') or docs_raw.startswith("'''"):
                docs_raw = docs_raw[3:]
            if docs_raw.endswith('"""') or docs_raw.endswith("'''"):
                docs_raw = docs_raw[:-3]
        self.docs = {
            "in": {
                "raw": docs_raw,
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
                "spaces": spaces + " " * kwargs.get("indent", 2),
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

        self.parse_definition()
        self.quotes = quotes

    def __str__(self):
        # for debuging
        txt = "\n\n** " + str(self.element["name"])
        txt += " of type " + str(self.element["deftype"]) + ":"
        txt += str(self.docs["in"]["desc"]) + "\n"
        txt += "->" + str(self.docs["in"]["params"]) + "\n"
        txt += "***>>" + str(self.docs["out"]["raw"]) + "\n" + "\n"
        return txt

    def __repr__(self):
        return self.__str__()

    def get_input_docstring(self):
        """Get the input raw docstring.

        Args:

        Returns:
          str or None: the input docstring if any.

        Raises:

        """
        return self.docs["in"]["raw"]

    def get_input_style(self):
        """Get the input docstring style

        Args:

        Returns:
          style: str: the style for input docstring

        Raises:

        """
        # TODO: use a getter
        return self.dst.style["in"]

    def set_input_style(self, style):
        """Sets the input docstring style

        Args:
          style(str): style to set for input docstring

        Returns:

        Raises:

        """
        # TODO: use a setter
        self.dst.style["in"] = style

    def get_output_style(self):
        """Sets the output docstring style

        Args:

        Returns:
          style: str: the style for output docstring

        Raises:

        """
        # TODO: use a getter
        return self.dst.style["out"]

    def set_output_style(self, style):
        """Sets the output docstring style

        Args:
          style(str): style to set for output docstring

        Returns:

        Raises:

        """
        # TODO: use a setter
        self.dst.style["out"] = style

    def get_spaces(self):
        """Get the output docstring initial spaces.

        Args:

        Returns:
          the spaces

        Raises:

        """
        return self.docs["out"]["spaces"]

    def set_spaces(self, spaces):
        """Set for output docstring the initial spaces.

        Args:
          spaces: the spaces to set

        Returns:

        Raises:

        """
        self.docs["out"]["spaces"] = spaces

    def parse_definition(self, raw=None):
        """Parses the element's elements (type, name and parameters) :)
        e.g.: def methode(param1, param2='default')
        def                      -> type
        methode                  -> name
        param1, param2='default' -> parameters

        Args:
          raw: raw data of the element (def or class). If None will use `self.element['raw']` (Default value = None)

        Returns:

        Raises:

        """
        # TODO: retrieve return from element external code (in parameter)
        if raw is None:
            l = self.element["raw"].strip()
        else:
            l = raw.strip()
        is_class = False
        if l.startswith("async def ") or l.startswith("def ") or l.startswith("class "):
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

    def _remove_signature_comment(self, txt):
        """If there is a comment at the end of the signature statement, remove it

        Args:
          txt:

        Returns:

        Raises:

        """
        ret = ""
        inside = None
        end_inside = {"(": ")", "{": "}", "[": "]", "'": "'", '"': '"'}
        for c in txt:
            if (inside and end_inside[inside] != c) or (
                not inside and c in end_inside.keys()
            ):
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

    def _extract_signature_elements(self, txt):
        """

        Args:
          txt:

        Returns:

        Raises:

        """
        start = txt.find("(") + 1
        end_start = txt.rfind(")")
        end_end = txt.rfind(":")
        return_type = (
            txt[end_start + 1 : end_end]
            .replace(" ", "")
            .replace("\t", "")
            .replace("->", "")
        )
        elems = {}
        elem_idx = 0
        reading = "param"
        elems[elem_idx] = {"type": "", "param": "", "default": ""}
        inside = None
        end_inside = {"(": ")", "{": "}", "[": "]", "'": "'", '"': '"'}
        for c in txt[start:end_start]:
            if (inside and end_inside[inside] != c) or (
                not inside and c in end_inside.keys()
            ):
                if not inside:
                    inside = c
                if reading == "type":
                    elems[elem_idx]["type"] += c
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
            if inside and c == end_inside[inside]:
                inside = None
            if reading == "param":
                if c not in ": ,=":
                    elems[elem_idx]["param"] += c
                else:
                    if c == " " and elems[elem_idx]["param"] or c != " ":
                        reading = "after_param"
            elif reading == "type":
                if c not in ",=":
                    elems[elem_idx]["type"] += c
                else:
                    reading = "after_type"
            elif reading == "default":
                if c != ",":
                    elems[elem_idx]["default"] += c
                else:
                    reading = "after_default"
            if reading.startswith("after_"):
                if reading == "after_param" and c == ":":
                    reading = "type"
                elif c == ",":
                    elem_idx += 1
                    elems[elem_idx] = {"type": "", "param": "", "default": ""}
                    reading = "param"
                elif c == "=":
                    reading = "default"
        # strip extracted elements
        for elem in elems:
            for subelem in elems[elem]:
                if type(elems[elem][subelem]) is str:
                    elems[elem][subelem] = elems[elem][subelem].strip()
        return {"parameters": elems, "return_type": return_type.strip()}

    def _extract_docs_doctest(self):
        """Extract the doctests if found.
        If there are doctests, they are removed from the input data and set on
        a specific buffer as they won't be altered.

        :return: True if found and proceeded else False

        Args:

        Returns:

        Raises:

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

    def _extract_docs_description(self):
        """Extract main description from docstring"""
        # FIXME: the indentation of descriptions is lost
        data = "\n".join(
            [
                d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                for d in self.docs["in"]["raw"].splitlines()
            ]
        )
        if self.dst.style["in"] == "groups":
            idx = self.dst.get_group_index(data)
        elif self.dst.style["in"] == "google":
            lines = data.splitlines()
            line_num = self.dst.googledoc.get_next_section_start_line(lines)
            if line_num == -1:
                idx = -1
            else:
                idx = len("\n".join(lines[:line_num]))
        elif self.dst.style["in"] == "numpydoc":
            lines = data.splitlines()
            line_num = self.dst.numpydoc.get_next_section_start_line(lines)
            if line_num == -1:
                idx = -1
            else:
                idx = len("\n".join(lines[:line_num]))
        elif self.dst.style["in"] == "unknown":
            idx = -1
        else:
            idx = self.dst.get_elem_index(data)
        if idx == 0:
            self.docs["in"]["desc"] = ""
        elif idx == -1:
            self.docs["in"]["desc"] = data
        else:
            self.docs["in"]["desc"] = data[:idx]

    def _extract_groupstyle_docs_params(self):
        """Extract group style parameters"""
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
        """ """
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
        """ """
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
        """Extract parameters description and type from docstring. The internal computed parameters list is
        composed by tuples (parameter, description, type).

        Args:

        Returns:

        Raises:

        """
        if self.dst.style["in"] == "numpydoc":
            data = "\n".join(
                [
                    d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                    for d in self.docs["in"]["raw"].splitlines()
                ]
            )
            self.docs["in"]["params"] += self.dst.numpydoc.get_param_list(data)
        elif self.dst.style["in"] == "google":
            data = "\n".join(
                [
                    d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                    for d in self.docs["in"]["raw"].splitlines()
                ]
            )
            self.docs["in"]["params"] += self.dst.googledoc.get_param_list(data)
        elif self.dst.style["in"] == "groups":
            self._extract_groupstyle_docs_params()
        elif self.dst.style["in"] in ["javadoc", "reST"]:
            self._extract_tagstyle_docs_params()

    def _extract_groupstyle_docs_raises(self):
        """ """
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
        """ """
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
        """Extract raises description from docstring. The internal computed raises list is
        composed by tuples (raise, description).

        Args:

        Returns:

        Raises:

        """
        if self.dst.style["in"] == "numpydoc":
            data = "\n".join(
                [
                    d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                    for d in self.docs["in"]["raw"].splitlines()
                ]
            )
            self.docs["in"]["raises"] += self.dst.numpydoc.get_raise_list(data)
        if self.dst.style["in"] == "google":
            data = "\n".join(
                [
                    d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                    for d in self.docs["in"]["raw"].splitlines()
                ]
            )
            self.docs["in"]["raises"] += self.dst.googledoc.get_raise_list(data)
        elif self.dst.style["in"] == "groups":
            self._extract_groupstyle_docs_raises()
        elif self.dst.style["in"] in ["javadoc", "reST"]:
            self._extract_tagstyle_docs_raises()

    def _extract_groupstyle_docs_return(self):
        """ """
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
        """ """
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
        """Extract return description and type"""
        if self.dst.style["in"] == "numpydoc":
            data = "\n".join(
                [
                    d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                    for d in self.docs["in"]["raw"].splitlines()
                ]
            )
            self.docs["in"]["return"] = self.dst.numpydoc.get_return_list(data)
            self.docs["in"]["rtype"] = None
        # TODO: fix this
        elif self.dst.style["in"] == "google":
            data = "\n".join(
                [
                    d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                    for d in self.docs["in"]["raw"].splitlines()
                ]
            )
            self.docs["in"]["return"] = self.dst.googledoc.get_return_list(data)
            self.docs["in"]["rtype"] = None
        elif self.dst.style["in"] == "groups":
            self._extract_groupstyle_docs_return()
        elif self.dst.style["in"] in ["javadoc", "reST"]:
            self._extract_tagstyle_docs_return()

    def _extract_docs_other(self):
        """Extract other specific sections"""
        if self.dst.style["in"] == "numpydoc":
            data = "\n".join(
                [
                    d.rstrip().replace(self.docs["out"]["spaces"], "", 1)
                    for d in self.docs["in"]["raw"].splitlines()
                ]
            )
            lst = self.dst.numpydoc.get_list_key(data, "also")
            lst = self.dst.numpydoc.get_list_key(data, "ref")
            lst = self.dst.numpydoc.get_list_key(data, "note")
            lst = self.dst.numpydoc.get_list_key(data, "other")
            lst = self.dst.numpydoc.get_list_key(data, "example")
            lst = self.dst.numpydoc.get_list_key(data, "attr")
            # TODO do something with this?

    def parse_docs(self, raw=None, before_lim=""):
        """Parses the docstring

        Args:
          raw: the data to parse if not internally provided (Default value = None)
          before_lim: specify raw or unicode or format docstring type (ie. "r" for r'''... or "fu" for fu'''...) (Default value = "")

        Returns:

        Raises:

        """
        self.before_lim = before_lim
        if raw is not None:
            raw = raw.strip()
            if raw.startswith('"""') or raw.startswith("'''"):
                raw = raw[3:]
            if raw.endswith('"""') or raw.endswith("'''"):
                raw = raw[:-3]
            self.docs["in"]["raw"] = raw
            self.dst.autodetect_style(raw)
        if self.docs["in"]["raw"] is None:
            return
        self.dst.params = self.element["params"]
        self._extract_docs_doctest()
        self._extract_docs_params()
        self._extract_docs_return()
        self._extract_docs_raises()
        self._extract_docs_description()
        self._extract_docs_other()
        self.parsed_docs = True

    def _set_desc(self):
        """Sets the global description if any"""
        # TODO: manage different in/out styles
        self.docs["out"]["desc"] = self.docs["in"]["desc"] or ""

    def _set_params(self):
        """Sets the parameters with types, descriptions and default value if any
        taken from the input docstring and the signature parameters

        Args:

        Returns:

        Raises:

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

    def _set_raises(self):
        """Sets the raises and descriptions"""
        # TODO: manage different in/out styles
        # manage setting if not mandatory for numpy but optional
        if self.docs["in"]["raises"]:
            if (
                self.dst.style["out"] != "numpydoc"
                or self.dst.style["in"] == "numpydoc"
                or (
                    self.dst.style["out"] == "numpydoc"
                    and "raise" not in self.dst.numpydoc.get_excluded_sections()
                )
            ):
                # list of parameters is like: (name, description)
                self.docs["out"]["raises"] = list(self.docs["in"]["raises"])

    def _set_return(self):
        """Sets the return parameter with description and rtype if any"""
        # TODO: manage return retrieved from element code (external)
        # TODO: manage different in/out styles
        if type(self.docs["in"]["return"]) is list and self.dst.style["out"] not in [
            "groups",
            "numpydoc",
            "google",
        ]:
            # TODO: manage return names
            # manage not setting return if not mandatory for numpy
            lst = self.docs["in"]["return"]
            if lst:
                if lst[0][0] is not None:
                    self.docs["out"]["return"] = "%s-> %s" % (lst[0][0], lst[0][1])
                else:
                    self.docs["out"]["return"] = lst[0][1]
                self.docs["out"]["rtype"] = lst[0][2]
        else:
            self.docs["out"]["return"] = self.docs["in"]["return"]
            self.docs["out"]["rtype"] = self.docs["in"]["rtype"]
        if (
            self._options["hint_rtype_priority"] or not self.docs["out"]["rtype"]
        ) and self.element["rtype"]:
            self.docs["out"]["rtype"] = self.element["rtype"]

    def _set_other(self):
        """Sets other specific sections"""
        # manage not setting if not mandatory for numpy
        if self.dst.style["in"] == "numpydoc":
            if self.docs["in"]["raw"] is not None:
                self.docs["out"]["post"] = self.dst.numpydoc.get_raw_not_managed(
                    self.docs["in"]["raw"]
                )
            elif "post" not in self.docs["out"] or self.docs["out"]["post"] is None:
                self.docs["out"]["post"] = ""

    def _set_raw_params(self, sep):
        """Set the output raw parameters section

        Args:
          sep: the separator of current style

        Returns:

        Raises:

        """
        raw = "\n"
        if self.dst.style["out"] == "numpydoc":
            spaces = " " * 4
            with_space = lambda s: "\n".join(
                [
                    self.docs["out"]["spaces"] + spaces + l.lstrip() if i > 0 else l
                    for i, l in enumerate(s.splitlines())
                ]
            )
            raw += self.dst.numpydoc.get_key_section_header(
                "param", self.docs["out"]["spaces"]
            )
            for p in self.docs["out"]["params"]:
                raw += self.docs["out"]["spaces"] + p[0] + " :"
                if p[2] is not None and len(p[2]) > 0:
                    raw += " " + p[2]
                raw += "\n"
                raw += self.docs["out"]["spaces"] + spaces + with_space(p[1]).strip()
                if len(p) > 2:
                    if (
                        "default" not in p[1].lower()
                        and len(p) > 3
                        and p[3] is not None
                    ):
                        raw += " (Default value = " + str(p[3]) + ")"
                raw += "\n"
        elif self.dst.style["out"] == "google":
            spaces = " " * 2
            with_space = lambda s: "\n".join(
                [
                    self.docs["out"]["spaces"] + l.lstrip() if i > 0 else l
                    for i, l in enumerate(s.splitlines())
                ]
            )
            raw += self.dst.googledoc.get_key_section_header(
                "param", self.docs["out"]["spaces"]
            )
            for p in self.docs["out"]["params"]:
                raw += self.docs["out"]["spaces"] + spaces + p[0]
                if p[2] is not None and len(p[2]) > 0:
                    raw += "(" + p[2]
                    if len(p) > 3 and p[3] is not None:
                        raw += ", optional"
                    raw += ")"
                raw += ": " + with_space(p[1]).strip()
                if len(p) > 2:
                    if (
                        "default" not in p[1].lower()
                        and len(p) > 3
                        and p[3] is not None
                    ):
                        raw += " (Default value = " + str(p[3]) + ")"
                raw += "\n"
        elif self.dst.style["out"] == "groups":
            pass
        else:
            with_space = lambda s: "\n".join(
                [
                    self.docs["out"]["spaces"] + l if i > 0 else l
                    for i, l in enumerate(s.splitlines())
                ]
            )
            if len(self.docs["out"]["params"]):
                for p in self.docs["out"]["params"]:
                    raw += (
                        self.docs["out"]["spaces"]
                        + self.dst.get_key("param", "out")
                        + " "
                        + p[0]
                        + sep
                        + with_space(p[1]).strip()
                    )
                    if len(p) > 2:
                        if (
                            "default" not in p[1].lower()
                            and len(p) > 3
                            and p[3] is not None
                        ):
                            raw += " (Default value = " + str(p[3]) + ")"
                        if p[2] is not None and len(p[2]) > 0:
                            raw += "\n"
                            raw += (
                                self.docs["out"]["spaces"]
                                + self.dst.get_key("type", "out")
                                + " "
                                + p[0]
                                + sep
                                + p[2]
                            )
                    if self.type_stub and (
                        len(p) <= 2 or p[2] is None or len(p[2]) == 0
                    ):
                        raw += "\n"
                        raw += (
                            self.docs["out"]["spaces"]
                            + self.dst.get_key("type", "out")
                            + " "
                            + p[0]
                            + sep
                        )
                    raw += "\n"
        return raw

    def _set_raw_raise(self, sep):
        """Set the output raw exception section

        Args:
          sep: the separator of current style

        Returns:

        Raises:

        """
        raw = ""
        if self.dst.style["out"] == "numpydoc":
            if "raise" not in self.dst.numpydoc.get_excluded_sections():
                raw += "\n"
                if "raise" in self.dst.numpydoc.get_mandatory_sections() or (
                    self.docs["out"]["raises"]
                    and "raise" in self.dst.numpydoc.get_optional_sections()
                ):
                    spaces = " " * 4
                    with_space = lambda s: "\n".join(
                        [
                            self.docs["out"]["spaces"] + spaces + l.lstrip()
                            if i > 0
                            else l
                            for i, l in enumerate(s.splitlines())
                        ]
                    )
                    raw += self.dst.numpydoc.get_key_section_header(
                        "raise", self.docs["out"]["spaces"]
                    )
                    if len(self.docs["out"]["raises"]):
                        for p in self.docs["out"]["raises"]:
                            raw += self.docs["out"]["spaces"] + p[0] + "\n"
                            raw += (
                                self.docs["out"]["spaces"]
                                + spaces
                                + with_space(p[1]).strip()
                                + "\n"
                            )
                    raw += "\n"
        elif self.dst.style["out"] == "google":
            if "raise" not in self.dst.googledoc.get_excluded_sections():
                raw += "\n"
                if "raise" in self.dst.googledoc.get_mandatory_sections() or (
                    self.docs["out"]["raises"]
                    and "raise" in self.dst.googledoc.get_optional_sections()
                ):
                    spaces = " " * 2
                    with_space = lambda s: "\n".join(
                        [
                            self.docs["out"]["spaces"] + spaces + l.lstrip()
                            if i > 0
                            else l
                            for i, l in enumerate(s.splitlines())
                        ]
                    )
                    raw += self.dst.googledoc.get_key_section_header(
                        "raise", self.docs["out"]["spaces"]
                    )
                    if len(self.docs["out"]["raises"]):
                        for p in self.docs["out"]["raises"]:
                            raw += self.docs["out"]["spaces"] + spaces
                            if p[0] is not None:
                                raw += p[0] + sep
                            if p[1]:
                                raw += p[1].strip()
                            raw += "\n"
                    raw += "\n"
        elif self.dst.style["out"] == "groups":
            pass
        else:
            with_space = lambda s: "\n".join(
                [
                    self.docs["out"]["spaces"] + l if i > 0 else l
                    for i, l in enumerate(s.splitlines())
                ]
            )
            if len(self.docs["out"]["raises"]):
                if not self.docs["out"]["params"] and not self.docs["out"]["return"]:
                    raw += "\n"
                for p in self.docs["out"]["raises"]:
                    raw += (
                        self.docs["out"]["spaces"]
                        + self.dst.get_key("raise", "out")
                        + " "
                    )
                    if p[0] is not None:
                        raw += p[0] + sep
                    if p[1]:
                        raw += with_space(p[1]).strip()
                    raw += "\n"
            raw += "\n"
        return raw

    def _set_raw_return(self, sep):
        """Set the output raw return section

        Args:
          sep: the separator of current style

        Returns:

        Raises:

        """
        raw = ""
        if self.dst.style["out"] == "numpydoc":
            raw += "\n"
            spaces = " " * 4
            with_space = lambda s: "\n".join(
                [
                    self.docs["out"]["spaces"] + spaces + l.lstrip() if i > 0 else l
                    for i, l in enumerate(s.splitlines())
                ]
            )
            raw += self.dst.numpydoc.get_key_section_header(
                "return", self.docs["out"]["spaces"]
            )
            if self.docs["out"]["rtype"]:
                rtype = self.docs["out"]["rtype"]
            else:
                rtype = "type"
            # case of several returns
            if type(self.docs["out"]["return"]) is list:
                for ret_elem in self.docs["out"]["return"]:
                    # if tuple (name, desc, rtype) else string desc
                    if type(ret_elem) is tuple and len(ret_elem) == 3:
                        rtype = ret_elem[2]
                        if rtype is None:
                            rtype = ""
                        raw += self.docs["out"]["spaces"]
                        if ret_elem[0]:
                            raw += ret_elem[0] + " : "
                        raw += (
                            rtype
                            + "\n"
                            + self.docs["out"]["spaces"]
                            + spaces
                            + with_space(ret_elem[1]).strip()
                            + "\n"
                        )
                    else:
                        # There can be a problem
                        raw += self.docs["out"]["spaces"] + rtype + "\n"
                        raw += (
                            self.docs["out"]["spaces"]
                            + spaces
                            + with_space(str(ret_elem)).strip()
                            + "\n"
                        )
            # case of a unique return
            elif self.docs["out"]["return"] is not None:
                raw += self.docs["out"]["spaces"] + rtype
                raw += (
                    "\n"
                    + self.docs["out"]["spaces"]
                    + spaces
                    + with_space(self.docs["out"]["return"]).strip()
                    + "\n"
                )
        elif self.dst.style["out"] == "google":
            raw += "\n"
            spaces = " " * 2
            with_space = lambda s: "\n".join(
                [
                    self.docs["out"]["spaces"] + spaces + l.lstrip() if i > 0 else l
                    for i, l in enumerate(s.splitlines())
                ]
            )
            raw += self.dst.googledoc.get_key_section_header(
                "return", self.docs["out"]["spaces"]
            )
            if self.docs["out"]["rtype"]:
                rtype = self.docs["out"]["rtype"]
            else:
                rtype = None
            # case of several returns
            if type(self.docs["out"]["return"]) is list:
                for ret_elem in self.docs["out"]["return"]:
                    # if tuple (name=None, desc, rtype) else string desc
                    if type(ret_elem) is tuple and len(ret_elem) == 3:
                        rtype = ret_elem[2]
                        if rtype is None:
                            rtype = ""
                        raw += self.docs["out"]["spaces"] + spaces
                        raw += rtype + ": " + with_space(ret_elem[1]).strip() + "\n"
                    else:
                        # There can be a problem
                        if rtype:
                            raw += self.docs["out"]["spaces"] + spaces + rtype + ": "
                            raw += with_space(str(ret_elem)).strip() + "\n"
                        else:
                            raw += (
                                self.docs["out"]["spaces"]
                                + spaces
                                + with_space(str(ret_elem)).strip()
                                + "\n"
                            )
            # case of a unique return
            elif self.docs["out"]["return"] is not None:
                if rtype:
                    raw += self.docs["out"]["spaces"] + spaces + rtype + ": "
                    raw += with_space(self.docs["out"]["return"]).strip() + "\n"
                else:
                    raw += (
                        self.docs["out"]["spaces"]
                        + spaces
                        + with_space(self.docs["out"]["return"]).strip()
                        + "\n"
                    )
        elif self.dst.style["out"] == "groups":
            pass
        else:
            with_space = lambda s: "\n".join(
                [
                    self.docs["out"]["spaces"] + l if i > 0 else l
                    for i, l in enumerate(s.splitlines())
                ]
            )
            if self.docs["out"]["return"]:
                if not self.docs["out"]["params"]:
                    raw += "\n"
                raw += (
                    self.docs["out"]["spaces"]
                    + self.dst.get_key("return", "out")
                    + sep
                    + with_space(self.docs["out"]["return"].rstrip()).strip()
                    + "\n"
                )
            if self.docs["out"]["rtype"]:
                if not self.docs["out"]["params"]:
                    raw += "\n"
                raw += (
                    self.docs["out"]["spaces"]
                    + self.dst.get_key("rtype", "out")
                    + sep
                    + self.docs["out"]["rtype"].rstrip()
                    + "\n"
                )
        return raw

    def _set_raw(self):
        """Sets the output raw docstring"""
        sep = self.dst.get_sep(target="out")
        sep = sep + " " if sep != " " else sep
        with_space = lambda s: "\n".join(
            [
                self.docs["out"]["spaces"] + l if i > 0 else l
                for i, l in enumerate(s.splitlines())
            ]
        )

        # sets the description section
        raw = self.docs["out"]["spaces"] + self.before_lim + self.quotes
        desc = self.docs["out"]["desc"].strip()
        if not desc or not desc.count("\n"):
            if (
                not self.docs["out"]["params"]
                and not self.docs["out"]["return"]
                and not self.docs["out"]["rtype"]
                and not self.docs["out"]["raises"]
            ):
                raw += desc if desc else self.trailing_space
                raw += self.quotes
                self.docs["out"]["raw"] = raw.rstrip()
                return
        if not self.first_line:
            raw += "\n" + self.docs["out"]["spaces"]
        raw += with_space(self.docs["out"]["desc"]).strip() + "\n"

        # sets the parameters section
        raw += self._set_raw_params(sep)

        # sets the return section
        raw += self._set_raw_return(sep)

        # sets the raises section
        raw += self._set_raw_raise(sep)

        # sets post specific if any
        if "post" in self.docs["out"]:
            raw += (
                self.docs["out"]["spaces"]
                + with_space(self.docs["out"]["post"]).strip()
                + "\n"
            )

        # sets the doctests if any
        if "doctests" in self.docs["out"]:
            raw += (
                self.docs["out"]["spaces"]
                + with_space(self.docs["out"]["doctests"]).strip()
                + "\n"
            )

        if raw.count(self.quotes) == 1:
            raw += self.docs["out"]["spaces"] + self.quotes
        self.docs["out"]["raw"] = raw.rstrip()

    def generate_docs(self):
        """Generates the output docstring"""
        if (
            self.dst.style["out"] == "numpydoc"
            and self.dst.numpydoc.first_line is not None
        ):
            self.first_line = self.dst.numpydoc.first_line
        self._set_desc()
        self._set_params()
        self._set_return()
        self._set_raises()
        self._set_other()
        self._set_raw()
        self.generated_docs = True

    def get_raw_docs(self):
        """Generates raw docstring

        Args:

        Returns:
          the raw docstring

        Raises:

        """
        if not self.generated_docs:
            self.generate_docs()
        return self.docs["out"]["raw"]


if __name__ == "__main__":
    help(DocString)
