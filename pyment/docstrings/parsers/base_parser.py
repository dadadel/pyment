"""Module containing the parsing base class."""

from typing import Dict, Iterator, List, Optional, Tuple

from pyment.docstrings.helpers import get_leading_spaces


class DocToolsBase:
    """Base class for parsing docstrings.."""

    def __init__(
        self,
        optional_sections: Tuple[str, ...] = (),
        excluded_sections: Tuple[str, ...] = (),
        opt: Optional[Dict[str, str]] = None,
        section_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Init.

        Parameters
        ----------
        optional_sections : Optional[Tuple[str, ...]]
            list of sections that are not mandatory (Default value = None)
        excluded_sections : Optional[Tuple[str, ...]]
            list of sections that are excluded, (Default value = None)
        opt : Optional[Dict[str, str]]
            _description_ (Default value = None)
        section_headers : Optional[Dict[str, str]]
            _description_ (Default value = None)
        """
        self.optional_sections = list(optional_sections)
        self.excluded_sections = list(excluded_sections)
        self.opt = opt or {}
        self.section_headers = section_headers or {}

    def __iter__(self) -> Iterator[str]:
        """Iterate over self.opt.

        Returns
        -------
        Iterator[str]
            iterator over self.opt
        """
        return self.opt.__iter__()

    def __getitem__(self, key: str) -> str:
        """Get from self.opt.

        Parameters
        ----------
        key : str
            Key to get value for

        Returns
        -------
        str
            Value from self.opt
        """
        return self.opt[key]

    def get_optional_sections(self) -> List[str]:
        """Get optional sections.

        Returns
        -------
        List[str]
            optional_sections
        """
        return self.optional_sections

    def get_excluded_sections(self) -> List[str]:
        """Get excluded sections.

        Returns
        -------
        List[str]
            excluded_sections
        """
        return self.excluded_sections

    def get_mandatory_sections(self) -> List[str]:
        """Get mandatory sections.

        Returns
        -------
        List[str]
            Mandatory sections.
        """
        return [
            s
            for s in self.opt
            if s not in self.optional_sections and s not in self.excluded_sections
        ]

    def _get_list_key(
        self, _spaces: str, _lines: List[str]
    ) -> List[Tuple[Optional[str], str, Optional[str]]]:
        """Parse lines and extract the list of key elements.

        Delegates to child classes.

        Parameters
        ----------
        spaces : str
            leading spaces of starting line
        lines : List[str]
            list of strings

        Returns
        -------
        List[Tuple[Optional[str], str, Optional[str]]]
            list of key elements
        """
        raise NotImplementedError

    def get_list_key(
        self, data: str, key: str, header_lines: int = 1
    ) -> List[Tuple[Optional[str], str, Optional[str]]]:
        """Get the list of a key elements.

        Each element is a tuple (key=None, description, type=None).
        Note that the tuple's element can differ depending on the key.

        Parameters
        ----------
        data : str
            the data to proceed
        key : str
            the key
        header_lines : int
            How many lines the header is long (Default value = 1)

        Returns
        -------
        List[Tuple[Optional[str],str,Optional[str]]]
            _description_
        """
        # Split the data into lines
        data_list = data.splitlines()
        # Get the line that that section starts at
        init = self.get_section_key_line(data_list, key)
        # If it can not be found at all return the empty list
        if init == -1:
            return []
        # If we could find it we want to grab all of its lines starting from there
        start, end = self.get_next_section_lines(data_list[init:])
        # get the spacing of line with key
        spaces = get_leading_spaces(data_list[init + start])
        # The start of the actual paragraph is start+init + how long the header is
        start += init + header_lines
        if end != -1:
            end += init
        else:
            end = len(data_list)
        # So now we grab the actual lines
        return self._get_list_key(spaces, data_list[start:end])

    def get_raise_list(self, data: str) -> List[Tuple[str, str]]:
        """Get the list of exceptions.

        The list contains tuples (name, desc).

        Parameters
        ----------
        data : str
            the data to proceed

        Returns
        -------
        List[Tuple[str,str]]
            _description_
        """
        raises_list = self.get_list_key(data, "raise")
        # Currently ignoring pyright here.
        # Have to figure out how to properly handle overloads between
        # child and parent classes here.
        return [
            (name, desc)  # pyright: ignore [reportGeneralTypeIssues]
            for name, desc, _ in raises_list
        ]

    def get_return_list(
        self, data: str
    ) -> List[Tuple[Optional[str], str, Optional[str]]]:
        """Get the list of returned values.

        The list contains tuples (name=None, desc, type=None).

        Parameters
        ----------
        data : str
            the data to proceed

        Returns
        -------
        List[Tuple[Optional[str],str,Optional[str]]]
            List of returned values.
        """
        result_list = []
        for name, desc, rtype in self.get_list_key(data, "return"):
            # If the input is named then we have for numpy style
            #   description
            # If not it is
            # type
            #   description
            # So the value of type is None, the value of name holds the actual type
            if rtype is None:
                result_list.append((None, desc.strip(), name))
            else:
                result_list.append((name, desc, rtype))

        return result_list

    def get_param_list(self, data: str) -> List[Tuple[str, str, Optional[str]]]:
        """Get the list of parameters.

        The list contains tuples (name, desc, type=None).

        Parameters
        ----------
        data : str
            the data to proceed

        Returns
        -------
        List[Tuple[str,str,Optional[str]]]
            List of parameters
        """
        return self.get_list_key(
            data, "param"  # pyright: ignore [reportGeneralTypeIssues]
        )

    def get_next_section_start_line(self, _data: List[str]) -> int:
        """Get the starting line number of next section.

        Delegates to child classes.

        It will return -1 if no section was found.
        The section is a section key (e.g. 'Parameters:')
        then the content.

        Parameters
        ----------
        data : List[str]
            a list of strings containing the docstring's lines

        Returns
        -------
        int
            the index of next section else -1
        """
        raise NotImplementedError

    def get_next_section_lines(self, data: List[str]) -> Tuple[int, int]:
        """Get the starting line number and the ending line number of next section.

        It will return (-1, -1) if no section was found.
        The section is a section key (e.g. 'Parameters') then the content
        The ending line number is the line after the end of the section or -1 if
        the section is at the end.

        Parameters
        ----------
        data : List[str]
            the data to proceed

        Returns
        -------
        Tuple[int,int]
            Line numbers of next section
        """
        # Get the start of the next section
        start = self.get_next_section_start_line(data)
        end = (
            # If there was a start then we grab the start of the line after as the end
            # Then the next section is contained in [start, end)
            self.get_next_section_start_line(data[start + 1 :])
            if start != -1
            else -1
        )
        return start, end

    def get_key_section_header(self, key: str, _spaces: str) -> str:
        """Get the key of the section header.

        Parameters
        ----------
        key : str
            the key name

        Returns
        -------
        str
            Key for the section header
        """
        if key in self.section_headers:
            header = self.section_headers[key]
        else:
            return ""

        return header

    def get_section_key_line(
        self, data: List[str], key: str, opt_extension: str = ""
    ) -> int:
        """Get the next section line for a given key.

        Parameters
        ----------
        data : List[str]
            the data to proceed
        key : str
            the key
        opt_extension : str
            an optional extension to delimit the opt value (Default value = "")

        Returns
        -------
        int
            Section key line.
        """
        start = 0  # The index of the starting line of the desired section
        init = 0
        while start != -1:
            # Gives the index of the line on which the next section starts
            # Returns -1 if there is no more section start until the end of `data`
            start = self.get_next_section_start_line(data[init:])
            init += start
            # Dont do this if no next section was found
            if start != -1:
                # If if the section that was found is the one we looked for
                # we break
                if data[init].strip().lower() == self.opt[key] + opt_extension:
                    break
                # If it is not we increment by one and keep looking from there
                init += 1
        # If we found the start when we update start to be that line index
        if start != -1:
            start = init
        # If not it stays as -1 and we return that.
        # Should probably honestly be None but whatever
        return start
