"""Module containing the parser for google docstrings."""

from typing import List, Optional, Tuple

from pyment.docstrings.helpers import get_leading_spaces, isin_alone

from .base_parser import DocToolsBase


class GoogledocTools(DocToolsBase):
    """_summary_."""

    def __init__(
        self,
        optional_sections: Tuple[str, ...] = ("raise",),
        excluded_sections: Tuple[str, ...] = (),
    ) -> None:
        """_summary_.

        Parameters
        ----------
        optional_sections : list
            list of sections that are not mandatory (Default value = ("raise"))
            The accepted sections are:
                -param
                -return
                -raise
        excluded_sections : list
            list of sections that are excluded, (Default value = ())
        """
        super().__init__(
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

    def get_section_key_line(
        self, data: str, key: str, opt_extension: str = ":"
    ) -> int:
        """Get the next section line for a given key.

        Parameters
        ----------
        data : str
            the data to proceed
        key : str
            the key
        opt_extension :str
            an optional extension to delimit the opt value (Default value = ":")

        Returns
        -------
        int
            _description_
        """
        return super().get_section_key_line(
            data, key, opt_extension  # pyright: ignore [reportGeneralTypeIssues]
        )

    def _get_list_key(  # noqa: PLR0912
        self, spaces: str, lines: str
    ) -> List[Tuple[Optional[str], str, Optional[str]]]:
        """_summary_.

        Parameters
        ----------
        spaces : str
            _description_
        lines : str
            _description_

        Returns
        -------
        _type_
            _description_
        """
        key_list = []
        parse_key = False
        key, desc, ptype = None, "", None
        param_spaces = 0

        for line in lines:
            if len(line.strip()) == 0:
                continue
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
                        line = line.replace(spaces, "", 1)  # noqa: PLW2901
                    if desc:
                        desc += "\n"
                    desc += line
            else:
                if len(curr_spaces) > len(spaces):
                    line = line.replace(spaces, "", 1)  # noqa: PLW2901
                if desc:
                    desc += "\n"
                desc += line
        if parse_key or desc:
            key_list.append((key, desc, ptype))

        return key_list

    def get_next_section_start_line(self, data: List[str]) -> int:
        """Get the starting line number of next section.

        It will return -1 if no section was found.
        The section is a section key (e.g. 'Parameters:')
        then the content.

        Parameters
        ----------
        data : List[str]
            a list of strings containing the docstring's lines

        Returns
        -------
        _type_
            the index of next section else -1
        """
        return next(
            (
                i
                for i, line in enumerate(data)
                if isin_alone([f"{k}:" for k in self.opt.values()], line)
            ),
            -1,
        )

    def get_key_section_header(self, key: str, spaces: str) -> str:
        """Get the key of the section header.

        Parameters
        ----------
        key : str
            the key name
        spaces : str
            spaces to set at the beginning of the header

        Returns
        -------
        str
            _description_
        """
        header = super().get_key_section_header(key, spaces)
        return spaces + header + ":" + "\n"
