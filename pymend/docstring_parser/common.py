"""Common methods for parsing."""

import enum
from dataclasses import dataclass
from typing import Optional, Union

from typing_extensions import TypeAlias

PARAM_KEYWORDS = {
    "param",
    "parameter",
    "arg",
    "argument",
    "attribute",
    "key",
    "keyword",
}
# These could be made into frozen sets
# Then one could create a dictionary
# {KEYWORD: FUNCTION_THAT_HANDLES_THAT_KEYWORD_SECTION}  # noqa: ERA001
RAISES_KEYWORDS = {"raises", "raise", "except", "exception"}
DEPRECATION_KEYWORDS = {"deprecation", "deprecated"}
RETURNS_KEYWORDS = {"return", "returns"}
YIELDS_KEYWORDS = {"yield", "yields"}
EXAMPLES_KEYWORDS = {"example", "examples"}


def clean_str(string: str) -> Optional[str]:
    """Strip a string and return None if it is now empty.

    Parameters
    ----------
    string : str
        String to clean

    Returns
    -------
    Optional[str]
        None of the stripped string is empty. Otherwise the stripped string.
    """
    string = string.strip()
    return string if string != "" else None


class ParseError(RuntimeError):
    """Base class for all parsing related errors."""


class DocstringStyle(enum.Enum):
    """Docstring style."""

    REST = 1
    GOOGLE = 2
    NUMPYDOC = 3
    EPYDOC = 4
    AUTO = 255


class RenderingStyle(enum.Enum):
    """Rendering style when unparsing parsed docstrings."""

    COMPACT = 1
    CLEAN = 2
    EXPANDED = 3


@dataclass
class DocstringMeta:
    """Docstring meta information.

    Symbolizes lines in form of

    Parameters
    ----------
    args : List[str]
        list of arguments. The exact content of this variable is
        dependent on the kind of docstring; it's used to distinguish
        between custom docstring meta information items.
    description : Optional[str]
        associated docstring description.
    """

    args: list[str]
    description: Optional[str]


@dataclass
class DocstringParam(DocstringMeta):
    """DocstringMeta symbolizing :param metadata."""

    arg_name: str
    type_name: Optional[str]
    is_optional: Optional[bool]
    default: Optional[str]


@dataclass
class DocstringReturns(DocstringMeta):
    """DocstringMeta symbolizing :returns metadata."""

    type_name: Optional[str]
    is_generator: bool
    return_name: Optional[str] = None


@dataclass
class DocstringYields(DocstringMeta):
    """DocstringMeta symbolizing :yields metadata."""

    type_name: Optional[str]
    is_generator: bool
    yield_name: Optional[str] = None


@dataclass
class DocstringRaises(DocstringMeta):
    """DocstringMeta symbolizing :raises metadata."""

    type_name: Optional[str]


MainSections: TypeAlias = Union[
    DocstringParam, DocstringRaises, DocstringReturns, DocstringYields
]


@dataclass
class DocstringDeprecated(DocstringMeta):
    """DocstringMeta symbolizing deprecation metadata."""

    version: Optional[str]


@dataclass
class DocstringExample(DocstringMeta):
    """DocstringMeta symbolizing example metadata."""

    snippet: Optional[str]


class Docstring:
    """Docstring object representation."""

    def __init__(
        self,
        style: Optional[DocstringStyle] = None,
    ) -> None:
        """Initialize self.

        Parameters
        ----------
        style : Optional[DocstringStyle]
            Style that this docstring was formatted in. (Default value = None)
        """
        self.short_description: Optional[str] = None
        self.long_description: Optional[str] = None
        self.blank_after_short_description: bool = False
        self.blank_after_long_description: bool = False
        self.meta: list[DocstringMeta] = []
        self.style: Optional[DocstringStyle] = style

    @property
    def params(self) -> list[DocstringParam]:
        """Return a list of information on function params.

        Returns
        -------
        list[DocstringParam]
            list of information on function params
        """
        return [item for item in self.meta if isinstance(item, DocstringParam)]

    @property
    def raises(self) -> list[DocstringRaises]:
        """Return a list of the exceptions that the function may raise.

        Returns
        -------
        list[DocstringRaises]
            list of the exceptions that the function may raise.
        """
        return [item for item in self.meta if isinstance(item, DocstringRaises)]

    @property
    def returns(self) -> Optional[DocstringReturns]:
        """Return a single information on function return.

        Takes the first return information.

        Returns
        -------
        Optional[DocstringReturns]
            Single information on function return.
        """
        return next(
            (item for item in self.meta if isinstance(item, DocstringReturns)),
            None,
        )

    @property
    def many_returns(self) -> list[DocstringReturns]:
        """Return a list of information on function return.

        Returns
        -------
        list[DocstringReturns]
            list of information on function return.
        """
        return [item for item in self.meta if isinstance(item, DocstringReturns)]

    @property
    def yields(self) -> Optional[DocstringYields]:
        """Return information on function yield.

        Takes the first generator information.

        Returns
        -------
        Optional[DocstringYields]
            Single information on function yield.
        """
        return next(
            (
                item
                for item in self.meta
                if isinstance(item, DocstringYields) and item.is_generator
            ),
            None,
        )

    @property
    def many_yields(self) -> list[DocstringYields]:
        """Return a list of information on function yields.

        Returns
        -------
        list[DocstringYields]
            list of information on function yields.
        """
        return [item for item in self.meta if isinstance(item, DocstringYields)]

    @property
    def deprecation(self) -> Optional[DocstringDeprecated]:
        """Return a single information on function deprecation notes.

        Returns
        -------
        Optional[DocstringDeprecated]
            single information on function deprecation notes.
        """
        return next(
            (item for item in self.meta if isinstance(item, DocstringDeprecated)),
            None,
        )

    @property
    def examples(self) -> list[DocstringExample]:
        """Return a list of information on function examples.

        Returns
        -------
        list[DocstringExample]
            list of information on function examples.
        """
        return [item for item in self.meta if isinstance(item, DocstringExample)]


def split_description(docstring: Docstring, desc_chunk: str) -> None:
    """Break description into short and long parts.

    Parameters
    ----------
    docstring : Docstring
        Docstring to fill with description information.
    desc_chunk : str
        Chunk of the raw docstring representing the description.
    """
    parts = desc_chunk.split("\n", 1)
    docstring.short_description = parts[0] or None
    if len(parts) > 1:
        long_desc_chunk = parts[1] or ""
        docstring.blank_after_short_description = long_desc_chunk.startswith("\n")
        docstring.blank_after_long_description = long_desc_chunk.endswith("\n\n")
        docstring.long_description = long_desc_chunk.strip() or None


def append_description(docstring: Docstring, parts: list[str]) -> None:
    """Append the docstrings description to the output stream.

    Parameters
    ----------
    docstring : Docstring
        Docstring whose information should be added.
    parts : list[str]
        List of strings representing the output of compose().
        Descriptions should be added to this.
    """
    if docstring.short_description:
        parts.append(docstring.short_description)
    if docstring.blank_after_short_description:
        parts.append("")
    if docstring.long_description:
        parts.append(docstring.long_description)
    if docstring.blank_after_long_description:
        parts.append("")
