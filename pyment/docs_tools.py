import re
from collections import defaultdict

from pyment.google_doc_tools import GoogledocTools
from pyment.numpy_doc_tools import NumpydocTools
from pyment.utils import isin, isin_alone, isin_start

RAISES_NAME_REGEX = r"^([\w.]+)"


class DocsTools:
    """This class provides the tools to manage several types of docstring.
    Currently the following are managed:
    - 'javadoc': javadoc style
    - 'reST': restructured text style compatible with Sphinx
    - 'groups': parameters on beginning of lines (like Google Docs)
    - 'google': the numpy format for docstrings (using an external module)
    - 'numpydoc': the numpy format for docstrings (using an external module)

    Args:

    Returns:

    Raises:

    """

    # TODO: enhance style dependent separation
    # TODO: add set methods to generate style specific outputs
    # TODO: manage C style (\param)
    def __init__(self, style_in="javadoc", style_out="reST", params=None):
        """Choose the kind of docstring type.

        :param style_in: docstring input style ('javadoc', 'reST', 'groups', 'numpydoc', 'google')
        :type style_in: string
        :param style_out: docstring output style ('javadoc', 'reST', 'groups', 'numpydoc', 'google')
        :type style_out: string
        :param params: if known the parameters names that should be found in the docstring.
        :type params: list

        """
        self.style = {"in": style_in, "out": style_out}
        self.opt = {}
        self.tagstyles = []
        self._set_available_styles()
        self.params = params
        self.numpydoc = NumpydocTools()
        self.googledoc = GoogledocTools()

    def _set_available_styles(self):
        """Set the internal styles list and available options in a structure as following:

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

        Args:

        Returns:

        Raises:

        """
        options_tagstyle = {
            "keys": ["param", "type", "returns", "return", "rtype", "raise"],
            "styles": {
                "javadoc": ("@", ":"),  # tuple:  key prefix, separator
                "reST": (":", ":"),
                "cstyle": ("\\", " "),
            },
        }
        self.tagstyles = list(options_tagstyle["styles"].keys())
        for op in options_tagstyle["keys"]:
            self.opt[op] = {}
            for style in options_tagstyle["styles"]:
                self.opt[op][style] = {
                    "name": options_tagstyle["styles"][style][0] + op,
                    "sep": options_tagstyle["styles"][style][1],
                }
        self.opt["return"]["reST"]["name"] = ":returns"
        self.opt["raise"]["reST"]["name"] = ":raises"
        self.groups = {
            "param": ["params", "args", "parameters", "arguments"],
            "return": ["returns", "return"],
            "raise": ["raises", "exceptions", "raise", "exception"],
        }

    def autodetect_style(self, data):
        """Determine the style of a docstring,
        and sets it as the default input one for the instance.

        Args:
          data(str): the docstring's data to recognize.

        Returns:
          str: the style detected else 'unknown'

        Raises:

        """
        # evaluate styles with keys

        found_keys = defaultdict(int)
        for style in self.tagstyles:
            for key in self.opt:
                found_keys[style] += data.count(self.opt[key][style]["name"])
        fkey = max(found_keys, key=found_keys.get)
        detected_style = fkey if found_keys[fkey] else "unknown"

        # evaluate styles with groups

        if detected_style == "unknown":
            found_groups = 0
            found_googledoc = 0
            found_numpydoc = 0
            found_numpydocsep = 0
            for line in data.strip().splitlines():
                for key in self.groups:
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
        self.style["in"] = detected_style

        return detected_style

    def set_input_style(self, style):
        """Set the input docstring style

        Args:
          style(str): style to set for input docstring

        Returns:

        Raises:

        """
        self.style["in"] = style

    def set_output_style(self, style):
        """Set the output docstring style

        Args:
          style(str): style to set for output docstring

        Returns:

        Raises:

        """
        self.style["out"] = style

    def _get_options(self, style):
        """Get the list of keywords for a particular style

        Args:
          style: the style that the keywords are wanted

        Returns:

        Raises:

        """
        return [self.opt[o][style]["name"] for o in self.opt]

    def get_key(self, key, target="in"):
        """Get the name of a key in current style.
        e.g.: in javadoc style, the returned key for 'param' is '@param'

        Args:
          key: the key wanted (param, type, return, rtype,..)
          target: the target docstring is 'in' for the input or
        'out' for the output to generate. (Default value = 'in')

        Returns:

        Raises:

        """
        target = "out" if target == "out" else "in"
        return self.opt[key][self.style[target]]["name"]

    def get_sep(self, key="param", target="in"):
        """Get the separator of current style.
        e.g.: in reST and javadoc style, it is ":"

        Args:
          key: the key which separator is wanted (param, type, return, rtype,..) (Default value = 'param')
          target: the target docstring is 'in' for the input or
        'out' for the output to generate. (Default value = 'in')

        Returns:

        Raises:

        """
        target = "out" if target == "out" else "in"
        if self.style[target] in ["numpydoc", "google"]:
            return ""
        return self.opt[key][self.style[target]]["sep"]

    def get_doctests_indexes(self, data):
        """Extract Doctests if found and return it

        Args:
          data: string to parse

        Returns:
          tuple: index of start and index of end of the doctest, else (-1, -1)

        Raises:

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

    def get_group_key_line(self, data, key):
        """Get the next group-style key's line number.

        Args:
          data: string to parse
          key: the key category

        Returns:
          the found line number else -1

        Raises:

        """
        idx = -1
        for i, line in enumerate(data.splitlines()):
            if isin_start(self.groups[key], line):
                idx = i
        return idx

    #        search = '\s*(%s)' % '|'.join(self.groups[key])
    #        m = re.match(search, data.lower())
    #        if m:
    #            key_param = m.group(1)

    def get_group_key_index(self, data, key):
        """Get the next groups style's starting line index for a key

        Args:
          data: string to parse
          key: the key category

        Returns:
          the index if found else -1

        Raises:

        """
        idx = -1
        li = self.get_group_key_line(data, key)
        if li != -1:
            idx = 0
            for line in data.splitlines()[:li]:
                idx += len(line) + len("\n")
        return idx

    def get_group_line(self, data):
        """Get the next group-style key's line.

        Args:
          data: the data to proceed

        Returns:
          the line number

        Raises:

        """
        idx = -1
        for key in self.groups:
            i = self.get_group_key_line(data, key)
            if (i < idx and i != -1) or idx == -1:
                idx = i
        return idx

    def get_group_index(self, data):
        """Get the next groups style's starting line index

        Args:
          data: string to parse

        Returns:
          the index if found else -1

        Raises:

        """
        idx = -1
        li = self.get_group_line(data)
        if li != -1:
            idx = 0
            for line in data.splitlines()[:li]:
                idx += len(line) + len("\n")
        return idx

    def get_key_index(self, data, key, starting=True):
        """Get from a docstring the next option with a given key.

        Args:
          data: string to parse
          key: the key category. Can be 'param', 'type', 'return', ...
          starting(boolean, optional): does the key element must start the line (Default value = True)

        Returns:
          integer: index of found element else -1

        Raises:

        """
        key = self.opt[key][self.style["in"]]["name"]
        if key.startswith(":returns"):
            data = data.replace(":return:", ":returns:")  # see issue 9
        idx = len(data)
        ini = 0
        loop = True
        if key in data:
            while loop:
                i = data.find(key)
                if i != -1:
                    if starting:
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
                else:
                    loop = False
        if idx == len(data):
            idx = -1
        return idx

    def get_elem_index(self, data, starting=True):
        """Get from a docstring the next option.
        In javadoc style it could be @param, @return, @type,...

        Args:
          data: string to parse
          starting(boolean, optional): does the key element must start the line (Default value = True)

        Returns:
          integer: index of found element else -1

        Raises:

        """
        idx = len(data)
        for opt in self.opt.keys():
            i = self.get_key_index(data, opt, starting)
            if i < idx and i != -1:
                idx = i
        if idx == len(data):
            idx = -1
        return idx

    def get_elem_desc(self, data, key):
        """TODO

        Args:
          data:
          key:

        Returns:

        Raises:

        """

    def get_elem_param(self):
        """TODO"""

    def get_raise_indexes(self, data):
        """Get from a docstring the next raise name indexes.
        In javadoc style it is after @raise.

        Args:
          data: string to parse

        Returns:
          tuple: start and end indexes of found element else (-1, -1)
          or else (-2, -2) if try to use params style but no parameters were provided.
          Note: the end index is the index after the last name character

        Raises:

        """
        start, end = -1, -1
        stl_param = self.opt["raise"][self.style["in"]]["name"]
        if self.style["in"] in self.tagstyles + ["unknown"]:
            idx_p = self.get_key_index(data, "raise")
            if idx_p >= 0:
                idx_p += len(stl_param)
                m = re.match(RAISES_NAME_REGEX, data[idx_p:].strip())
                if m:
                    param = m.group(1)
                    start = idx_p + data[idx_p:].find(param)
                    end = start + len(param)

        if self.style["in"] in ["groups", "unknown"] and (start, end) == (-1, -1):
            # search = '\s*(%s)' % '|'.join(self.groups['param'])
            # m = re.match(search, data.lower())
            # if m:
            #    key_param = m.group(1)
            pass

        return start, end

    def get_raise_description_indexes(self, data, prev=None):
        """Get from a docstring the next raise's description.
        In javadoc style it is after @param.

        Args:
          data: string to parse
          prev: index after the param element name (Default value = None)

        Returns:
          tuple: start and end indexes of found element else (-1, -1)

        Raises:

        """
        start, end = -1, -1
        if not prev:
            _, prev = self.get_raise_indexes(data)
        if prev < 0:
            return -1, -1
        m = re.match(r"\W*(\w+)", data[prev:])
        if m:
            first = m.group(1)
            start = data[prev:].find(first)
            if start >= 0:
                start += prev
                if self.style["in"] in self.tagstyles + ["unknown"]:
                    end = self.get_elem_index(data[start:])
                    if end >= 0:
                        end += start
                if self.style["in"] in ["params", "unknown"] and end == -1:
                    p1, _ = self.get_raise_indexes(data[start:])
                    if p1 >= 0:
                        end = p1
                    else:
                        end = len(data)

        return start, end

    def _extra_tagstyle_elements(self, data):
        """

        Args:
          data:

        Returns:

        Raises:

        """
        ret = {}
        style_param = self.opt["param"][self.style["in"]]["name"]
        style_type = self.opt["type"][self.style["in"]]["name"]
        # fixme for return and raise, ignore last char as there's an optional 's' at the end and they are not managed in this function
        style_return = self.opt["return"][self.style["in"]]["name"][:-1]
        style_raise = self.opt["raise"][self.style["in"]]["name"][:-1]
        last_element = {"nature": None, "name": None}
        for line in data.splitlines():
            param_name = None
            param_type = None
            param_description = None
            param_part = None
            # parameter statement
            if line.strip().startswith(style_param):
                last_element["nature"] = "param"
                last_element["name"] = None
                line = line.strip().replace(style_param, "", 1).strip()
                if ":" in line:
                    param_part, param_description = line.split(":", 1)
                else:
                    print("WARNING: malformed docstring parameter")
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
                line = line.strip().replace(style_type, "", 1).strip()
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
            else:
                # suppose to be line of a multiline element
                if last_element["nature"] == "param":
                    ret[last_element["name"]]["description"] += f"\n{line}"
                elif last_element["nature"] == "type":
                    ret[last_element["name"]]["description"] += f"\n{line}"
        return ret

    def _extract_not_tagstyle_old_way(self, data):
        """

        Args:
          data:

        Returns:

        Raises:

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
                        f"WARNING: unexpected parsing duplication of docstring parameter '{param}'"
                    )
                ret[param] = {"type": ptype, "type_in_param": None, "description": desc}
                data = data[end:]
                listed += 1
            else:
                loop = False
        if i > maxi:
            print(
                "WARNING: an infinite loop was reached while extracting docstring parameters (>10000). This should never happen!!!"
            )
        return ret

    def extract_elements(self, data) -> dict:
        """Extract parameter name, description and type from docstring

        Args:
          data:

        Returns:

        Raises:

        """
        ret = []
        tagstyles = self.tagstyles + ["unknown"]
        if self.style["in"] in tagstyles:
            ret = self._extra_tagstyle_elements(data)
        else:
            # fixme enhance management of other styles
            ret = self._extract_not_tagstyle_old_way(data)
        return ret

    def get_param_indexes(self, data):
        """Get from a docstring the next parameter name indexes.
        In javadoc style it is after @param.

        Args:
          data: string to parse

        Returns:
          tuple: start and end indexes of found element else (-1, -1)
          or else (-2, -2) if try to use params style but no parameters were provided.
          Note: the end index is the index after the last name character

        Raises:

        """
        # TODO: new method to extract an element's name so will be available for @param and @types and other styles (:param, \param)
        start, end = -1, -1
        stl_param = self.opt["param"][self.style["in"]]["name"]
        if self.style["in"] in self.tagstyles + ["unknown"]:
            idx_p = self.get_key_index(data, "param")
            if idx_p >= 0:
                idx_p += len(stl_param)
                m = re.match(r"^([\w]+)", data[idx_p:].strip())
                if m:
                    param = m.group(1)
                    start = idx_p + data[idx_p:].find(param)
                    end = start + len(param)

        if self.style["in"] in ["groups", "unknown"] and (start, end) == (-1, -1):
            # search = '\s*(%s)' % '|'.join(self.groups['param'])
            # m = re.match(search, data.lower())
            # if m:
            #    key_param = m.group(1)
            pass

        if self.style["in"] in ["params", "groups", "unknown"] and (start, end) == (
            -1,
            -1,
        ):
            if not self.params:
                return -2, -2
            idx = -1
            param = None
            for p in self.params:
                p = p["param"]
                i = data.find("\n" + p)
                if i >= 0:
                    if idx == -1 or i < idx:
                        idx = i
                        param = p
            if idx != -1:
                start, end = idx, idx + len(param)
        return start, end

    def get_param_description_indexes(self, data, prev=None):
        """Get from a docstring the next parameter's description.
        In javadoc style it is after @param.

        Args:
          data: string to parse
          prev: index after the param element name (Default value = None)

        Returns:
          tuple: start and end indexes of found element else (-1, -1)

        Raises:

        """
        start, end = -1, -1
        if not prev:
            _, prev = self.get_param_indexes(data)
        if prev < 0:
            return -1, -1
        m = re.match(r"\W*(\w+)", data[prev:])
        if m:
            first = m.group(1)
            start = data[prev:].find(first)
            if start >= 0:
                if "\n" in data[prev : prev + start]:
                    # avoid to get next element as a description
                    return -1, -1
                start += prev
                if self.style["in"] in self.tagstyles + ["unknown"]:
                    end = self.get_elem_index(data[start:])
                    if end >= 0:
                        end += start
                if self.style["in"] in ["params", "unknown"] and end == -1:
                    p1, _ = self.get_param_indexes(data[start:])
                    if p1 >= 0:
                        end = p1
                    else:
                        end = len(data)

        return start, end

    def get_param_type_indexes(self, data, name=None, prev=None):
        """Get from a docstring a parameter type indexes.
        In javadoc style it is after @type.

        Args:
          data: string to parse
          name: the name of the parameter (Default value = None)
          prev: index after the previous element (param or param's description) (Default value = None)

        Returns:
          tuple: start and end indexes of found element else (-1, -1)
          Note: the end index is the index after the last included character or -1 if
          reached the end

        Raises:

        """
        start, end = -1, -1
        stl_type = self.opt["type"][self.style["in"]]["name"]
        if not prev:
            _, prev = self.get_param_description_indexes(data)
        if prev >= 0:
            if self.style["in"] in self.tagstyles + ["unknown"]:
                idx = self.get_elem_index(data[prev:])
                if idx >= 0 and data[prev + idx :].startswith(stl_type):
                    idx = prev + idx + len(stl_type)
                    m = re.match(r"\W*(\w+)\W+(\w+)\W*", data[idx:].strip())
                    if m:
                        param = m.group(1).strip()
                        if (name and param == name) or not name:
                            desc = m.group(2)
                            start = data[idx:].find(desc) + idx
                            end = self.get_elem_index(data[start:])
                            if end >= 0:
                                end += start

            if self.style["in"] in ["params", "unknown"] and (start, end) == (-1, -1):
                # TODO: manage this
                pass

        return start, end

    def get_return_description_indexes(self, data):
        """Get from a docstring the return parameter description indexes.
        In javadoc style it is after @return.

        Args:
          data: string to parse

        Returns:
          tuple: start and end indexes of found element else (-1, -1)
          Note: the end index is the index after the last included character or -1 if
          reached the end

        Raises:

        """
        start, end = -1, -1
        stl_return = self.opt["return"][self.style["in"]]["name"]
        if self.style["in"] in self.tagstyles + ["unknown"]:
            idx = self.get_key_index(data, "return")
            idx_abs = idx
            # search starting description
            if idx >= 0:
                # FIXME: take care if a return description starts with <, >, =,...
                m = re.match(r"\W*(\w+)", data[idx_abs + len(stl_return) :])
                if m:
                    first = m.group(1)
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

        if self.style["in"] in ["params", "unknown"] and (start, end) == (-1, -1):
            # TODO: manage this
            pass

        return start, end

    def get_return_type_indexes(self, data):
        """Get from a docstring the return parameter type indexes.
        In javadoc style it is after @rtype.

        Args:
          data: string to parse

        Returns:
          tuple: start and end indexes of found element else (-1, -1)
          Note: the end index is the index after the last included character or -1 if
          reached the end

        Raises:

        """
        start, end = -1, -1
        stl_rtype = self.opt["rtype"][self.style["in"]]["name"]
        if self.style["in"] in self.tagstyles + ["unknown"]:
            dstart, dend = self.get_return_description_indexes(data)
            # search the start
            if dstart >= 0 and dend > 0:
                idx = self.get_elem_index(data[dend:])
                if idx >= 0 and data[dend + idx :].startswith(stl_rtype):
                    idx = dend + idx + len(stl_rtype)
                    m = re.match(r"\W*(\w+)", data[idx:])
                    if m:
                        first = m.group(1)
                        start = data[idx:].find(first) + idx
            # search the end
            idx = self.get_elem_index(data[start:])
            if idx > 0:
                end = idx + start

        if self.style["in"] in ["params", "unknown"] and (start, end) == (-1, -1):
            # TODO: manage this
            pass

        return start, end
