from more_itertools import pairwise, split_before

from pyment.doc_tools_base import DocToolsBase
from pyment.utils import get_leading_spaces, isin_alone


class NumpydocTools(DocToolsBase):
    """ """

    HEADER_LINES = 2

    def __init__(
        self,
        first_line=None,
        optional_sections=(
            "raise",
            "also",
            "ref",
            "note",
            "other",
            "example",
            "method",
            "attr",
        ),
        excluded_sections=(),
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
          -also
          -ref
          -note
          -other
          -example
          -method
          -attr
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

        self.keywords = [
            ":math:",
            ".. math::",
            "see also",
            ".. image::",
        ]

    def get_next_section_start_line(self, data):
        """Get the starting line number of next section.
        It will return -1 if no section was found.
        The section is a section key (e.g. 'Parameters') followed by underline
        (made by -), then the content

        Args:
          data(list(str): a list of strings containing the docstring's lines

        Returns:
          : the index of next section else -1

        Raises:

        """
        for i, (line, next_line) in enumerate(pairwise(data)):
            if (
                isin_alone(self.opt.values(), line)
                and "-" * len(line.strip()) == next_line.strip()
            ):
                return i
        return -1

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
        non_empty_lines = filter(lambda line: line.strip(), lines)

        for paragraph in split_before(
            non_empty_lines,
            lambda line: len(get_leading_spaces(line)) == len(spaces),
        ):
            elems = paragraph[0].split(":", 1)
            key = elems[0].strip()
            ptype = elems[1].strip() if len(elems) > 1 else None
            desc = "\n".join(
                line.replace(spaces, "", 1)
                if len(get_leading_spaces(line)) > len(spaces)
                else line
                for line in paragraph[1:]
            )

            key_list.append((key, desc, ptype))
        return key_list

    def get_raw_not_managed(self, data):
        """Get elements not managed. They can be used as is.

        Args:
          data: the data to proceed

        Returns:

        Raises:

        """
        keys = ["also", "ref", "note", "other", "example", "method", "attr"]
        elems = [self.opt[k] for k in self.opt if k in keys]
        data = data.splitlines()
        start = 0
        init = 0
        raw = ""
        spaces = None
        while start != -1:
            start, end = self.get_next_section_lines(data[init:])
            if start != -1:
                init += start
                if isin_alone(elems, data[init]) and not isin_alone(
                    [self.opt[e] for e in self.excluded_sections], data[init]
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
                    raw += "\n".join(section) + "\n"
                init += 2
        return raw

    def get_key_section_header(self, key, spaces):
        """Get the key of the header section

        Args:
          key: the key name
          spaces: spaces to set at the beginning of the header

        Returns:

        Raises:

        """
        header = super().get_key_section_header(key, spaces)
        header = spaces + header + "\n" + spaces + "-" * len(header) + "\n"
        return header
