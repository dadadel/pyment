from pyment.doc_tools_base import DocToolsBase
from pyment.utils import get_leading_spaces, isin_alone


class GoogledocTools(DocToolsBase):
    """ """

    def __init__(
        self, first_line=None, optional_sections=("raise"), excluded_sections=()
    ):
        """
        :param first_line: indicate if description should start
          on first or second line. By default it will follow global config.
        :type first_line: boolean
        :param optional_sections: list of sections that are not mandatory
          if empty. The accepted sections are:
          -param
          -return
          -raise
        :type optional_sections: list
        :param excluded_sections: list of sections that are excluded,
          even if mandatory. The list is the same than for optional sections.
        :type excluded_sections: list

        """
        super().__init__(
            first_line=first_line,
            optional_sections=optional_sections,
            excluded_sections=excluded_sections,
            opt={
                "attr": "attributes",
                "param": "args",
                "raise": "raises",
                "return": "returns",
                "yield": "yields",
            },
            section_headers={
                "param": "Args",
                "return": "Returns",
                "raise": "Raises",
            },
        )

    def get_section_key_line(self, data, key, opt_extension=":"):
        """Get the next section line for a given key.

        Args:
          data: the data to proceed
          key: the key
          opt_extension: an optional extension to delimit the opt value (Default value = ":")

        Returns:

        Raises:

        """
        return super().get_section_key_line(data, key, opt_extension)

    def _get_list_key(self, spaces, lines):
        """Parse lines and extract the list of key elements.

        Args:
          spaces(str): leading spaces of starting line
          lines(list(str): list of strings

        Returns:
          : list of key elements

        Raises:

        """
        key_list = []
        parse_key = False
        key, desc, ptype = None, "", None
        param_spaces = 0

        non_empty_lines = filter(lambda line: line.strip(), lines)

        for line in non_empty_lines:
            curr_spaces = get_leading_spaces(line)
            if not param_spaces:
                param_spaces = len(curr_spaces)
            if len(curr_spaces) == param_spaces:
                if parse_key:
                    key_list.append((key, desc, ptype))
                if ":" in line:
                    elems = line.split(":", 1)
                    ptype = None
                    key = elems[0].strip()
                    # the param's type is near the key in parenthesis
                    if "(" in key and ")" in key:
                        tstart = key.index("(") + 1
                        tend = key.index(")")
                        # the 'optional' keyword can follow the style after a comma
                        if "," in key:
                            tend = key.index(",")
                        ptype = key[tstart:tend].strip()
                        key = key[: tstart - 1].strip()
                    desc = elems[1].strip()
                    parse_key = True
                else:
                    if len(curr_spaces) > len(spaces):
                        line = line.replace(spaces, "", 1)
                    if desc:
                        desc += "\n"
                    desc += line
            else:
                if len(curr_spaces) > len(spaces):
                    line = line.replace(spaces, "", 1)
                if desc:
                    desc += "\n"
                desc += line
        if parse_key or desc:
            key_list.append((key, desc, ptype))

        return key_list

    def get_next_section_start_line(self, data):
        """Get the starting line number of next section.
        It will return -1 if no section was found.
        The section is a section key (e.g. 'Parameters:')
        then the content

        Args:
          data: a list of strings containing the docstring's lines

        Returns:
          : the index of next section else -1

        Raises:

        """
        start = -1
        for i, line in enumerate(data):
            if isin_alone([k + ":" for k in self.opt.values()], line):
                start = i
                break
        return start

    def get_key_section_header(self, key, spaces):
        """Get the key of the section header

        Args:
          key: the key name
          spaces: spaces to set at the beginning of the header

        Returns:

        Raises:

        """
        header = super().get_key_section_header(key, spaces)
        header = spaces + header + ":" + "\n"
        return header
