from pyment.utils import get_leading_spaces


class DocToolsBase:
    """ """

    HEADER_LINES = 1

    def __init__(
        self,
        first_line=None,
        optional_sections=None,
        excluded_sections=None,
        opt=None,
        section_headers=None,
    ):
        """

        :param first_line: indicate if description should start
          on first or second line. By default it will follow global config.
        :type first_line: boolean
        :param optional_sections: list of sections that are not mandatory
          if empty. See subclasses for further description.
        :type optional_sections: list
        :param excluded_sections: list of sections that are excluded,
          even if mandatory. The list is the same as for optional sections.
        :type excluded_sections: list
        :param opt:
        :type opt:
        :param section_headers:
        :type section_headers:
        """
        self.first_line = first_line
        self.optional_sections = list(optional_sections)
        self.excluded_sections = list(excluded_sections)
        self.opt = opt
        self.section_headers = section_headers

    def __iter__(self):
        return self.opt.__iter__()

    def __getitem__(self, key):
        return self.opt[key]

    def get_optional_sections(self):
        """Get optional sections"""
        return self.optional_sections

    def get_excluded_sections(self):
        """Get excluded sections"""
        return self.excluded_sections

    def get_mandatory_sections(self):
        """Get mandatory sections"""
        return [
            s
            for s in self.opt
            if s not in self.optional_sections and s not in self.excluded_sections
        ]

    def _get_list_key(self, spaces, lines):
        """Parse lines and extract the list of key elements.

        Args:
          spaces(str): leading spaces of starting line
          lines(list(str): list of strings

        Returns:
          : list of key elements

        Raises:

        """
        raise NotImplementedError

    def get_list_key(self, data, key, header_lines=None):
        """Get the list of a key elements.
        Each element is a tuple (key=None, description, type=None).
        Note that the tuple's element can differ depending on the key.

        Args:
          data: the data to proceed
          key: the key
          header_lines: (Default value = 1)

        Returns:

        Raises:

        """
        if not header_lines:
            header_lines = self.HEADER_LINES
        data = data.splitlines()
        init = self.get_section_key_line(data, key)
        if init == -1:
            return []
        start, end = self.get_next_section_lines(data[init:])
        # get the spacing of line with key
        spaces = get_leading_spaces(data[init + start])
        start += init + header_lines
        if end != -1:
            end += init
        else:
            end = len(data)

        return self._get_list_key(spaces, data[start:end])

    def get_raise_list(self, data):
        """Get the list of exceptions.
        The list contains tuples (name, desc)

        Args:
          data: the data to proceed

        Returns:

        Raises:

        """
        return_list = []
        lst = self.get_list_key(data, "raise")
        for l in lst:
            # assume raises are only a name and a description
            name, desc, _ = l
            return_list.append((name, desc))

        return return_list

    def get_return_list(self, data):
        """Get the list of returned values.
        The list contains tuples (name=None, desc, type=None)

        Args:
          data: the data to proceed

        Returns:

        Raises:

        """
        return_list = []
        lst = self.get_list_key(data, "return")
        for l in lst:
            name, desc, rtype = l
            if l[2] is None:
                rtype = l[0]
                name = None
                desc = desc.strip()
            return_list.append((name, desc, rtype))

        return return_list

    def get_param_list(self, data):
        """Get the list of parameters.
        The list contains tuples (name, desc, type=None)

        Args:
          data: the data to proceed

        Returns:

        Raises:

        """
        return self.get_list_key(data, "param")

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
        raise NotImplementedError

    def get_next_section_lines(self, data):
        """Get the starting line number and the ending line number of next section.
        It will return (-1, -1) if no section was found.
        The section is a section key (e.g. 'Parameters') then the content
        The ending line number is the line after the end of the section or -1 if
        the section is at the end.

        Args:
          data: the data to proceed

        Returns:

        Raises:

        """
        end = -1
        start = self.get_next_section_start_line(data)
        if start != -1:
            end = self.get_next_section_start_line(data[start + 1 :])
        return start, end

    def get_key_section_header(self, key, spaces):
        """Get the key of the section header

        Args:
          key: the key name
          spaces: spaces to set at the beginning of the header

        Returns:

        Raises:

        """
        if key in self.section_headers:
            header = self.section_headers[key]
        else:
            return ""

        return header

    def get_section_key_line(self, data, key, opt_extension=""):
        """Get the next section line for a given key.

        Args:
          data: the data to proceed
          key: the key
          opt_extension: an optional extension to delimit the opt value (Default value = "")

        Returns:

        Raises:

        """
        start = 0
        init = 0
        while start != -1:
            start = self.get_next_section_start_line(data[init:])
            init += start
            if start != -1:
                if data[init].strip().lower() == self.opt[key] + opt_extension:
                    break
                init += 1
        if start != -1:
            start = init
        return start
