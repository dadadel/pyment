"""Module containing the parser for numpy docstrings."""

from typing import List, Optional, Tuple

from pyment.docstringssssss.helpers import get_leading_spaces, isin, isin_alone

from .base_parser import DocToolsBase


class NumpydocTools(DocToolsBase):
    """_summary_."""

    def __init__(
        self,
        optional_sections: Tuple[str, ...] = (
            "raise",
            "also",
            "ref",
            "note",
            "other",
            "example",
            "method",
            "attr",
        ),
        excluded_sections: Tuple[str, ...] = (),
    ) -> None:
        """_summary_.

        Parameters
        ----------
        optional_sections : Tuple[str, ...]
            list of sections that are not mandatory
            (Default value = ("raise","also","ref","note",
                "other","example","method","attr",))
            The accepted sections are:
                -param
                -return
                -raise
                -also
                -ref
                -note
                -other
                -example
                -method
                -attr
        excluded_sections : Tuple[str, ...]
            list of sections that are excluded, (Default value = ())
        """
        super().__init__(
            optional_sections=optional_sections,
            excluded_sections=excluded_sections,
            opt={
                "also": "see also",
                "attr": "attributes",
                "example": "examples",
                "method": "methods",
                "note": "notes",
                "other": "other parameters",
                "param": "parameters",
                "raise": "raises",
                "ref": "references",
                "return": "returns",
            },
            section_headers={
                "param": "Parameters",
                "return": "Returns",
                "raise": "Raises",
            },
        )
        # TODO: See how to actually make proper use of these
        # Probably need two separate lists here.
        # One for inline stuff and one that function as a full section
        # like deprecated
        self.keywords: List[str] = [
            ":math:",
            ".. math::",
            ".. image::",
        ]
        self.keyword_sections: List[str] = [".. deprecated::"]

    def get_next_section_start_line(self, data: List[str]) -> int:
        """Get the starting line number of next section.

        It will return -1 if no section was found.
        The section is a section key (e.g. 'Parameters') followed by underline
        (made by -), then the content.

        Parameters
        ----------
        data : List[str]
            a list of strings containing the docstring's lines

        Returns
        -------
        int
            the index of next section else -1
        """
        start = -1
        for i, line in enumerate(data):
            if start != -1:
                # we found the key so check if this is the underline
                if line.strip() and isin_alone(["-" * len(line.strip())], line):
                    break
                start = -1
            # We found one of our section header names
            # Mark start as i and in the next loop iteration
            # Check if we have the underline
            if isin_alone(self.opt.values(), line):
                start = i
            # We found one of our keyword_sections that are not followed by an underline
            # The keyword_sections entries also do not have to be alone on their line
            # .. deprecated:: Dont know when
            # Find out which function replaces it
            elif isin(self.keyword_sections, line):
                return i
        return start

    def get_list_key(
        self, data: str, key: str, header_lines: int = 2
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
            Number of header lines for a section (Default value = 2)

        Returns
        -------
        List[Tuple[str|None,str,str|None]]
            _description_
        """
        return super().get_list_key(data, key, header_lines=header_lines)

    def _get_list_key(
        self, spaces: str, lines: List[str]
    ) -> List[Tuple[Optional[str], str, Optional[str]]]:
        """_summary_.

        Parameters
        ----------
        spaces : str
            _description_
        lines : List[str]
            _description_

        Returns
        -------
        List[Tuple[str|None,str,str|None]]
            _description_
        """
        key_list: List[Tuple[Optional[str], str, Optional[str]]] = []
        parse_key: bool = False  # Tracks whether we are currently parsing a key
        key, desc, ptype = None, "", None

        # Go over each line one by one
        for line in lines:
            # If the line is just whitespace skip it
            if len(line.strip()) == 0:
                continue
            # on the same column of the key is the key
            curr_spaces = get_leading_spaces(line)
            # If the line has the same indentation as that of the header
            # then it should be a key entry
            # x : type   <---
            #    Description of parameter `x`.
            # y          <---
            #    Description of parameter `y` (with type not specified).
            if len(curr_spaces) == len(spaces):
                # If we are were already parsing a key
                # then add the previous one to the list
                if parse_key:
                    key_list.append((key, desc, ptype))
                # Fill the first entries for this key
                elems = line.split(":", 1)
                # Get name of param/return or type of exception
                key = elems[0].strip()
                # is type of param or return if present
                ptype = elems[1].strip() if len(elems) > 1 else None
                # Initialize description as empty
                desc = ""
                # We are now parsing a current entry
                parse_key = True
            else:
                # We are now parsing the description
                if len(curr_spaces) > len(spaces):
                    line = line.replace(spaces, "", 1)  # noqa: PLW2901
                if desc:
                    desc += "\n"
                desc += line
        # If we were parsing an entry at the end we also add that information
        if parse_key:
            key_list.append((key, desc, ptype))

        return key_list

    def get_attr_list(self, data: str) -> List[Tuple[str, str, str | None]]:
        """Get the list of attributes.

        The list contains tuples (name, desc, type=None).

        Parameters
        ----------
        data : _type_
            the data to proceed

        Returns
        -------
        List[Tuple[str | None, str, str | None]]
        """
        return self.get_list_key(
            data, "attr"  # pyright: ignore [reportGeneralTypeIssues]
        )

    def get_raw_not_managed(self, data_str: str) -> str:
        """Get elements not managed. They can be used as is.

        Parameters
        ----------
        data : str
            the data to proceed

        Returns
        -------
        str
            _description_
        """
        keys = ["also", "ref", "note", "other", "example", "method", "attr"]
        elems = [self.opt[k] for k in self.opt if k in keys]
        data = data_str.splitlines()
        start = 0
        init = 0
        raw = ""
        spaces = None
        while start != -1:
            start, end = self.get_next_section_lines(data[init:])
            if start != -1:
                init += start
                if (
                    isin_alone(elems, data[init])
                    and not isin_alone(
                        [self.opt[e] for e in self.excluded_sections], data[init]
                    )
                    or isin(self.keyword_sections, data[init])
                ):
                    spaces = get_leading_spaces(data[init])
                    if end != -1:
                        section = [
                            d.replace(spaces, "", 1).rstrip()
                            for d in data[init : init + end]
                        ]
                    else:
                        section = [
                            d.replace(spaces, "", 1).rstrip() for d in data[init:]
                        ]
                    raw += "\n\n" + "\n".join(section)
                init += 2
        return raw

    def get_key_section_header(self, key: str, spaces: str) -> str:
        """Get the key of the header section.

        Parameters
        ----------
        key : str
            the key name
        spaces : str
            spaces to set at the beginning of the header

        Returns
        -------
        str
            Header for the requested section.
        """
        header = super().get_key_section_header(key, spaces)
        return spaces + header + "\n" + spaces + "-" * len(header) + "\n"
