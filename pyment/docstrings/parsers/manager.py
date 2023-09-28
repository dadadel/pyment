"""Module for managing multiple types of docstrings."""

import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, TypedDict, Union

from pyment.docstrings.helpers import isin, isin_alone, isin_start

from .google_parser import GoogledocTools
from .numpy_parser import NumpydocTools

RAISES_NAME_REGEX = r"^([\w.]+)"


class Params(TypedDict):
    """Typedict for parameter info."""

    type: str
    param: str
    default: str


class TagstyleOptions(TypedDict):
    """Typeddict for tagstyle options."""

    keys: List[str]
    styles: Dict[str, Tuple[str, str]]


InputDocString = TypedDict(
    "InputDocString",
    {
        "raw": str,
        "pure_raw": str,
        "doctests": str,
        "desc": Optional[str],
        # (name, description, type) # noqa: ERA001
        "params": List[Tuple[str, str, Optional[str]]],
        "types": List[str],
        # The list contains tuples (name=None, desc, type=None)
        # If the input is named then we have for numpy style
        # name : type # noqa: ERA001
        #   description
        # If not it is
        # type
        #   description
        # So the value of type is None, the value of name holds the actual type
        "return": Union[Optional[str], List[Tuple[Optional[str], str, Optional[str]]]],
        "rtype": Optional[str],
        "raises": List[Tuple[str, str]],
    },
)

OutputDocString = TypedDict(
    "OutputDocString",
    {
        "raw": str,
        "desc": str,
        # (name, description, type, default) # noqa: ERA001
        "params": List[Tuple[str, str, Optional[str], Optional[str]]],
        "types": List[str],
        # The list contains tuples (name=None, desc, type=None)
        # If the input is named then we have for numpy style
        # name : type  # noqa: ERA001
        #   description
        # If not it is
        # type
        #   description
        # So the value of type is None, the value of name holds the actual type
        "return": Union[Optional[str], List[Tuple[Optional[str], str, Optional[str]]]],
        "rtype": Optional[str],
        "raises": List[Tuple[str, str]],
        "spaces": str,
        "doctests": str,
        "post": str,
    },
)


Docs = TypedDict("Docs", {"in": InputDocString, "out": OutputDocString})


class DocsTools:
    """Tools to manage several types of docstring.

    Currently the following are managed:
    - 'javadoc': javadoc style
    - 'reST': restructured text style compatible with Sphinx
    - 'groups': parameters on beginning of lines (like Google Docs)
    - 'google': the numpy format for docstrings (using an external module)
    - 'numpydoc': the numpy format for docstrings (using an external module).
    """

    # TODO: enhance style dependent separation
    # TODO: add set methods to generate style specific outputs
    # TODO: manage C style (\param)
    def __init__(
        self, style_in: str = "javadoc", params: Optional[List[Params]] = None
    ) -> None:
        """Choose the kind of docstring type.

        Parameters
        ----------
        style_in : str
            Docstring input style
            ('javadoc', 'reST', 'groups', 'numpydoc', 'google')
            (Default value = "javadoc")
        params : list
            If known the parameter names that should be found in the docstring.
            (Default value = None)
        """
        self.style = style_in
        self.opt = {}
        self.tagstyles = []
        self._set_available_styles()
        self.params = params
        self.numpydoc = NumpydocTools()
        self.googledoc = GoogledocTools()

    def _set_available_styles(self) -> None:
        """Set the internal styles list and available options.

            param: javadoc: name = '@param'
                            sep  = ':'
                   reST:    name = ':param'
                            sep  = ':'
                   ...
            type:  javadoc: name = '@type'
                            sep  = ':'
                   ...
            ...

        And sets the internal groups style:
            param:  'params', 'args', 'parameters', 'arguments'
            return: 'returns', 'return'
            raise:  'raises', 'raise', 'exceptions', 'exception'
        """
        options_tagstyle: TagstyleOptions = {
            "keys": ["param", "type", "returns", "return", "rtype", "raise"],
            "styles": {
                "javadoc": ("@", ":"),  # tuple:  key prefix, separator
                "reST": (":", ":"),
                "cstyle": ("\\", " "),
            },
        }
        self.tagstyles = list(options_tagstyle["styles"].keys())
        for option in options_tagstyle["keys"]:
            self.opt[option] = {}
            for style in options_tagstyle["styles"]:
                self.opt[option][style] = {
                    "name": options_tagstyle["styles"][style][0] + option,
                    "sep": options_tagstyle["styles"][style][1],
                }
        self.opt["return"]["reST"]["name"] = ":returns"
        self.opt["raise"]["reST"]["name"] = ":raises"
        self.groups = {
            "param": ["params", "args", "parameters", "arguments"],
            "return": ["returns", "return"],
            "raise": ["raises", "exceptions", "raise", "exception"],
        }

    def autodetect_style(self, data: str) -> str:
        """Determine the style of a docstring.

        Sets it as the default input one for the instance.

        Parameters
        ----------
        data : str
            the docstring's data to recognize.

        Returns
        -------
        str
            the style detected else 'unknown'
        """
        # evaluate styles with keys

        found_keys = defaultdict(int)
        for style in self.tagstyles:
            for option in self.opt.values():
                found_keys[style] += data.count(option[style]["name"])
        fkey = max(
            found_keys, key=found_keys.get  # pyright: ignore [reportGeneralTypeIssues]
        )
        detected_style = fkey if found_keys[fkey] else "unknown"

        # evaluate styles with groups
        if detected_style == "unknown":
            found_groups = 0
            found_googledoc = 0
            found_numpydoc = 0
            found_numpydocsep = 0
            for line in data.strip().splitlines():
                for key in self.groups:  # pylint: disable=consider-using-dict-items
                    found_groups += 1 if isin_start(self.groups[key], line) else 0
                for key in self.googledoc:
                    found_googledoc += 1 if isin_start(self.googledoc[key], line) else 0
                for key in self.numpydoc:
                    found_numpydoc += 1 if isin_start(self.numpydoc[key], line) else 0
                if line.strip() and isin_alone(["-" * len(line.strip())], line):
                    found_numpydocsep += 1
                elif isin(self.numpydoc.keywords, line):
                    found_numpydoc += 1
            # TODO: check if not necessary to have > 1??
            if found_numpydoc and found_numpydocsep:
                detected_style = "numpydoc"
            elif found_googledoc >= found_groups:
                detected_style = "google"
            elif found_groups:
                detected_style = "groups"
        self.style = detected_style

        return detected_style

    def set_input_style(self, style: str) -> None:
        """Set the input docstring style.

        Parameters
        ----------
        style : str
            style to set for input docstring
        """
        self.style = style

    def _get_options(self, style: str) -> List[str]:
        """Get the list of keywords for a particular style.

        Parameters
        ----------
        style : str
            the style that the keywords are wanted
        """
        return [
            self.opt[o][style]["name"]
            for o in self.opt  # pylint: disable=consider-using-dict-items
        ]

    def get_key(self, key: str, target: str = "in") -> str:
        """Get the name of a key in current style.

        e.g.: in javadoc style, the returned key for 'param' is

        Parameters
        ----------
        key : str
            the key wanted (param, type, return, rtype,..)
        target : str
            the target docstring is 'in' for the input or (Default value = "in")

        Returns
        -------
        str
            _description_
        """
        target = "numpydoc" if target == "out" else self.style
        return self.opt[key][target]["name"]

    def get_sep(self, key: str = "param", target: str = "in") -> str:
        """Get the separator of current style.

        e.g.: in reST and javadoc style, it is ":".

        Parameters
        ----------
        key : str
            the key which separator is wanted (param, type, return, rtype,..)
            (Default value = 'param')
        target : str
            the target docstring is 'in' for the input or (Default value = "in")

        Returns
        -------
        str
            Separator of the current style
        """
        target = "numpydoc" if target == "out" else self.style
        return "" if target in ["numpydoc", "google"] else self.opt[key][target]["sep"]

    def set_known_parameters(self, params: List[Params]) -> None:
        """Set known parameters names.

        Parameters
        ----------
        params : List[Params]
            the docstring parameters names
        """
        self.params = params

    def get_doctests_indexes(self, data: str) -> Tuple[int, int]:
        """Extract Doctests if found and return it.

        Parameters
        ----------
        data : str
            string to parse

        Returns
        -------
        Tuple[int,int]
            index of start and index of end of the doctest, else (-1, -1)
        """
        start, end = -1, -1
        datalst = data.splitlines()
        for i, line in enumerate(datalst):
            if start > -1:
                if line.strip() == "":
                    break
                end = i
            elif line.strip().startswith(">>>"):
                start = i
                end = i
        return start, end

    def get_group_key_line(self, data: str, key: str) -> int:
        """Get the next group-style key's line number.

        Parameters
        ----------
        data : str
            string to parse
        key : str
            the key category

        Returns
        -------
        _type_
            the found line number else -1
        """
        idx = -1
        for i, line in enumerate(data.splitlines()):
            if isin_start(self.groups[key], line):
                idx = i
        return idx

    def get_group_key_index(self, data: str, key: str) -> int:
        """Get the next groups style's starting line index for a key.

        Parameters
        ----------
        data : str
            string to parse
        key : str
            the key category

        Returns
        -------
        int
            the index if found else -1
        """
        line_number = self.get_group_key_line(data, key)
        return (
            sum(len(line) + len("\n") for line in data.splitlines()[:line_number])
            if line_number != -1
            else -1
        )

    def get_group_line(self, data: str) -> int:
        """Get the next group-style key's line.

        Parameters
        ----------
        data : str
            the data to proceed

        Returns
        -------
        int
            the line number
        """
        idx = -1
        for key in self.groups:
            i = self.get_group_key_line(data, key)
            if (i < idx and i != -1) or idx == -1:
                idx = i
        return idx

    def get_group_index(self, data: str) -> int:
        """Get the next groups style's starting line index.

        Parameters
        ----------
        data : str
            string to parse

        Returns
        -------
        int
            the index if found else -1
        """
        line_number = self.get_group_line(data)
        return (
            sum(len(line) + len("\n") for line in data.splitlines()[:line_number])
            if line_number != -1
            else -1
        )

    def get_key_index(self, data: str, key: str, *, starting: bool = True) -> int:
        """Get from a docstring the next option with a given key.

        Parameters
        ----------
        data : str
            string to parse
        key : str
            the key category. Can be 'param', 'type', 'return', ...
        starting : bool
            does the key element must start the line (Default value = True)

        Returns
        -------
        int
            index of found element else -1
        """
        key = self.opt[key][self.style]["name"]
        if key.startswith(":returns"):
            data = data.replace(":return:", ":returns:")  # see issue 9
        idx = len(data)
        ini = 0
        loop = True
        if key in data:
            while loop:
                i = data.find(key)
                if i == -1:
                    loop = False
                elif starting:
                    if (
                        not data[:i].rstrip(" \t").endswith("\n")
                        and len(data[:i].strip()) > 0
                    ):
                        ini = i + 1
                        data = data[ini:]
                    else:
                        idx = ini + i
                        loop = False
                else:
                    idx = ini + i
                    loop = False
        if idx == len(data):
            idx = -1
        return idx

    def get_elem_index(self, data: str, *, starting: bool = True) -> int:
        """Get from a docstring the next option.

        Parameters
        ----------
        data : str
            string to parse
        starting : bool
            does the key element have to start the line (Default value = True)

        Returns
        -------
        int
            index of found element else -1
        """
        idx = len(data)
        for opt in self.opt:
            i = self.get_key_index(data, opt, starting=starting)
            if i < idx and i != -1:
                idx = i
        if idx == len(data):
            idx = -1
        return idx

    def get_elem_desc(self, _data: str, _key: str) -> str:
        """TODO.

        Parameters
        ----------
        data : str
            _description_
        key : str
            _description_
        """
        return ""

    def get_elem_param(self) -> str:
        """TODO."""
        return ""

    def get_raise_indexes(self, data: str) -> Tuple[int, int]:
        """Get from a docstring the next raise name indexes.

        Parameters
        ----------
        data : str
            string to parse

        Returns
        -------
        Tuple[int,int]
            start and end indexes of found element else (-1, -1)
            or else (-2, -2) if try to use params style but no parameters were provided.
            Note: the end index is the index after the last name character
        """
        start, end = -1, -1
        if self.style in [*self.tagstyles, "unknown"]:
            idx_p = self.get_key_index(data, "raise")
            if idx_p >= 0:
                stl_param = self.opt["raise"][self.style]["name"]
                idx_p += len(stl_param)
                if matches := re.match(RAISES_NAME_REGEX, data[idx_p:].strip()):
                    param = matches[1]
                    start = idx_p + data[idx_p:].find(param)
                    end = start + len(param)

        return start, end

    def get_raise_description_indexes(
        self, data: str, prev: Optional[int] = None
    ) -> Tuple[int, int]:
        """Get from a docstring the next raise's description.

        Parameters
        ----------
        data : str
            string to parse
        prev : Optional[int]
            index after the param element name (Default value = None)

        Returns
        -------
        Tuple[int,int]
            start and end indexes of found element else (-1, -1)
        """
        start, end = -1, -1
        if not prev:
            _, prev = self.get_raise_indexes(data)
        if prev < 0:
            return -1, -1
        if matches := re.match(r"\W*(\w+)", data[prev:]):
            first = matches[1]
            start = data[prev:].find(first)
            if start >= 0:
                start += prev
                if self.style in [*self.tagstyles, "unknown"]:
                    end = self.get_elem_index(data[start:])
                    if end >= 0:
                        end += start
                if self.style in ["params", "unknown"] and end == -1:
                    start_index, _ = self.get_raise_indexes(data[start:])
                    end = start_index if start_index >= 0 else len(data)

        return start, end

    def _extra_tagstyle_elements(  # noqa: PLR0912, PLR0915
        self, data: str
    ) -> Dict[str, Dict[str, Optional[str]]]:
        """Extract parameter name, description and type from tagstyle docstring.

        Parameters
        ----------
        data : str
            docstring

        Returns
        -------
        Dict[str,Dict[str,Optional[str]]]
            _description_
        """
        ret = {}
        style_param = self.opt["param"][self.style]["name"]
        style_type = self.opt["type"][self.style]["name"]
        # fixme for return and raise,
        # ignore last char as there's an optional 's' at the end
        # and they are not managed in this function
        style_return = self.opt["return"][self.style]["name"][:-1]
        style_raise = self.opt["raise"][self.style]["name"][:-1]
        last_element = {"nature": None, "name": None}
        for line in data.splitlines():
            last_element: Dict[str, Optional[str]] = {"nature": None, "name": None}
            param_name = None
            param_type = None
            param_description = None
            param_part = ""
            # parameter statement
            if line.strip().startswith(style_param):
                last_element["nature"] = "param"
                last_element["name"] = None
                line = line.strip().replace(style_param, "", 1).strip()  # noqa: PLW2901
                if ":" in line:
                    param_part, param_description = line.split(":", 1)
                else:
                    print("WARNING: malformed docstring parameter")
                    continue
                res = re.split(r"\s+", param_part.strip())
                if len(res) == 1:
                    param_name = res[0].strip()
                elif len(res) == 2:
                    param_type, param_name = res[0].strip(), res[1].strip()
                else:
                    print("WARNING: malformed docstring parameter")
                if param_name:
                    # keep track in case of multiline
                    last_element["nature"] = "param"
                    last_element["name"] = param_name
                    if param_name not in ret:
                        ret[param_name] = {
                            "type": None,
                            "type_in_param": None,
                            "description": None,
                        }
                    if param_type:
                        ret[param_name]["type_in_param"] = param_type
                    if param_description:
                        ret[param_name]["description"] = param_description.strip()
                else:
                    print(
                        "WARNING: malformed docstring parameter: unable to extract name"
                    )
            # type statement
            elif line.strip().startswith(style_type):
                last_element["nature"] = "type"
                last_element["name"] = None
                line = line.strip().replace(style_type, "", 1).strip()  # noqa: PLW2901
                if ":" in line:
                    param_name, param_type = line.split(":", 1)
                    param_name = param_name.strip()
                    param_type = param_type.strip()
                else:
                    print("WARNING: malformed docstring parameter")
                if param_name:
                    # keep track in case of multiline
                    last_element["nature"] = "type"
                    last_element["name"] = param_name
                    if param_name not in ret:
                        ret[param_name] = {
                            "type": None,
                            "type_in_param": None,
                            "description": None,
                        }
                    if param_type:
                        ret[param_name]["type"] = param_type.strip()
            elif line.strip().startswith(style_raise) or line.startswith(style_return):
                # fixme not managed in this function
                last_element["nature"] = "raise-return"
                last_element["name"] = None
            # suppose to be line of a multiline element
            elif last_element["nature"] in ("param", "type"):
                ret[last_element["name"]]["description"] += f"\n{line}"
        return ret

    def _extract_not_tagstyle_old_way(
        self, data: str
    ) -> Dict[str, Dict[str, Optional[str]]]:
        """_summary_.

        Parameters
        ----------
        data : str
            _description_

        Returns
        -------
        Dict[str,Dict[str,Optional[str]]]
            _description_
        """
        ret = {}
        listed = 0
        loop = True
        maxi = 10000  # avoid infinite loop but should never happen
        i = 0
        while loop:
            i += 1
            if i > maxi:
                loop = False
            start, end = self.get_param_indexes(data)
            if start >= 0:
                param = data[start:end]
                desc = ""
                param_end = end
                start, end = self.get_param_description_indexes(data, prev=end)
                if start > 0:
                    desc = data[start:end].strip()
                if end == -1:
                    end = param_end
                ptype = ""
                start, pend = self.get_param_type_indexes(data, name=param, prev=end)
                if start > 0:
                    ptype = data[start:pend].strip()
                if param in ret:
                    print(
                        "WARNING: unexpected parsing duplication "
                        f"of docstring parameter '{param}'"
                    )
                ret[param] = {"type": ptype, "type_in_param": None, "description": desc}
                data = data[end:]
                listed += 1
            else:
                loop = False
        if i > maxi:
            print(
                "WARNING: an infinite loop was reached while extracting "
                "docstring parameters (>10000). This should never happen!!!"
            )
        return ret

    def extract_elements(self, data: str) -> Dict[str, Dict[str, Optional[str]]]:
        """Extract parameter name, description and type from docstring.

        Parameters
        ----------
        data : str
            docstring

        Returns
        -------
        Dict[str,Dict[str,Optional[str]]]
            _description_
        """
        tagstyles = [*self.tagstyles, "unknown"]
        # fixme enhance management of other styles
        return (
            self._extra_tagstyle_elements(data)
            if self.style in tagstyles
            else self._extract_not_tagstyle_old_way(data)
        )

    def get_param_indexes(self, data: str) -> Tuple[int, int]:
        """Get from a docstring the next parameter name indexes.

        Parameters
        ----------
        data : str
            string to parse

        Returns
        -------
        Tuple[int,int]
            start and end indexes of found element else (-1, -1)
            or else (-2, -2) if try to use params style but no parameters were provided.
            Note: the end index is the index after the last name character
        """
        # TODO: new method to extract an element's name so will be
        # available for @param and @types and other styles (:param, \param)
        start, end = -1, -1
        if self.style in [*self.tagstyles, "unknown"]:
            idx_p = self.get_key_index(data, "param")
            if idx_p >= 0:
                stl_param = self.opt["param"][self.style]["name"]
                idx_p += len(stl_param)
                if matches := re.match(r"^([\w]+)", data[idx_p:].strip()):
                    param = matches[1]
                    start = idx_p + data[idx_p:].find(param)
                    end = start + len(param)

        if self.style in ["params", "groups", "unknown"] and (start, end) == (
            -1,
            -1,
        ):
            if not self.params:
                return -2, -2
            idx = -1
            param = None
            for parameter in self.params:
                parameter_name = parameter["param"]
                i = data.find("\n" + parameter_name)
                if i >= 0 and (idx == -1 or i < idx):
                    idx = i
                    param = parameter_name
            if param is not None:  #  and idx != -1
                start, end = idx, idx + len(param)
        return start, end

    def get_param_description_indexes(
        self, data: str, prev: Optional[int] = None
    ) -> Tuple[int, int]:
        """Get from a docstring the next parameter's description.

        Parameters
        ----------
        data : str
            string to parse
        prev : Optional[int]
            index after the param element name (Default value = None)

        Returns
        -------
        Tuple[int,int]
            start and end indexes of found element else (-1, -1)
        """
        start, end = -1, -1
        if not prev:
            _, prev = self.get_param_indexes(data)
        if prev < 0:
            return -1, -1
        if matches := re.match(r"\W*(\w+)", data[prev:]):
            first = matches[1]
            start = data[prev:].find(first)
            if start >= 0:
                if "\n" in data[prev : prev + start]:
                    # avoid to get next element as a description
                    return -1, -1
                start += prev
                if self.style in [*self.tagstyles, "unknown"]:
                    end = self.get_elem_index(data[start:])
                    if end >= 0:
                        end += start
                if self.style in ["params", "unknown"] and end == -1:
                    start_index, _ = self.get_param_indexes(data[start:])
                    end = start_index if start_index >= 0 else len(data)

        return start, end

    def get_param_type_indexes(
        self, data: str, name: Optional[str] = None, prev: Optional[int] = None
    ) -> Tuple[int, int]:
        """Get from a docstring a parameter type indexes.

        Parameters
        ----------
        data : str
            string to parse
        name : Optional[str]
            the name of the parameter (Default value = None)
        prev : Optional[int]
            Index after the previous element (param or param's description)
            (Default value = None)

        Returns
        -------
        Tuple[int,int]
            start and end indexes of found element else (-1, -1)
            Note: the end index is the index after the last included character or -1 if
            reached the end
        """
        start, end = -1, -1
        stl_type = self.opt["type"][self.style]["name"]
        if not prev:
            _, prev = self.get_param_description_indexes(data)
        if prev >= 0 and self.style in [*self.tagstyles, "unknown"]:
            idx = self.get_elem_index(data[prev:])
            if idx >= 0 and data[prev + idx :].startswith(stl_type):
                idx = prev + idx + len(stl_type)
                if matches := re.match(r"\W*(\w+)\W+(\w+)\W*", data[idx:].strip()):
                    param = matches[1].strip()
                    if (name and param == name) or not name:
                        desc = matches[2]
                        start = data[idx:].find(desc) + idx
                        end = self.get_elem_index(data[start:])
                        if end >= 0:
                            end += start

        return start, end

    def get_return_description_indexes(self, data: str) -> Tuple[int, int]:
        """Get from a docstring the return parameter description indexes.

        Parameters
        ----------
        data : str
            string to parse

        Returns
        -------
        Tuple[int, int]
            start and end indexes of found element else (-1, -1)
            Note: the end index is the index after the last included character or -1 if
            reached the end
        """
        start, end = -1, -1
        stl_return = self.opt["return"][self.style]["name"]
        if self.style in [*self.tagstyles, "unknown"]:
            idx = self.get_key_index(data, "return")
            idx_abs = idx
            # search starting description
            if idx >= 0:
                if matches := re.match(r"\W*(\w+)", data[idx_abs + len(stl_return) :]):
                    first = matches[1]
                    idx = data[idx_abs:].find(first)
                    idx_abs += idx
                    start = idx_abs
                else:
                    idx = -1
            # search the end
            idx = self.get_elem_index(data[idx_abs:])
            if idx > 0:
                idx_abs += idx
                end = idx_abs

        return start, end

    def get_return_type_indexes(self, data: str) -> Tuple[int, int]:
        """Get from a docstring the return parameter type indexes.

        Parameters
        ----------
        data : str
            string to parse

        Returns
        -------
        Tuple[int,int]
            start and end indexes of found element else (-1, -1)
            Note: the end index is the index after the last included character or -1 if
            reached the end
        """
        start, end = -1, -1
        stl_rtype = self.opt["rtype"][self.style]["name"]
        if self.style in [*self.tagstyles, "unknown"]:
            dstart, dend = self.get_return_description_indexes(data)
            # search the start
            if dstart >= 0 and dend > 0:
                idx = self.get_elem_index(data[dend:])
                if idx >= 0 and data[dend + idx :].startswith(stl_rtype):
                    idx = dend + idx + len(stl_rtype)
                    if matches := re.match(r"\W*(\w+)", data[idx:]):
                        first = matches[1]
                        start = data[idx:].find(first) + idx
            # search the end
            idx = self.get_elem_index(data[start:])
            if idx > 0:
                end = idx + start

        return start, end
