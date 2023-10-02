"""Common methods for parsing."""
import enum
from dataclasses import dataclass
from typing import List, Optional

PARAM_KEYWORDS = {
    "param",
    "parameter",
    "arg",
    "argument",
    "attribute",
    "key",
    "keyword",
}
RAISES_KEYWORDS = {"raises", "raise", "except", "exception"}
DEPRECATION_KEYWORDS = {"deprecation", "deprecated"}
RETURNS_KEYWORDS = {"return", "returns"}
YIELDS_KEYWORDS = {"yield", "yields"}
EXAMPLES_KEYWORDS = {"example", "examples"}


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

    args: List[str]
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
    description: Optional[str]


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
        """Initialize self."""
        self.short_description: Optional[str] = None
        self.long_description: Optional[str] = None
        self.blank_after_short_description: bool = False
        self.blank_after_long_description: bool = False
        self.meta: List[DocstringMeta] = []
        self.style: Optional[DocstringStyle] = style

    @property
    def params(self) -> List[DocstringParam]:
        """Return a list of information on function params."""
        return [item for item in self.meta if isinstance(item, DocstringParam)]

    @property
    def raises(self) -> List[DocstringRaises]:
        """Return a list of the exceptions that the function may raise."""
        return [item for item in self.meta if isinstance(item, DocstringRaises)]

    @property
    def returns(self) -> Optional[DocstringReturns]:
        """Return a single information on function return.

        Takes the first return information.
        """
        return next(
            (item for item in self.meta if isinstance(item, DocstringReturns)),
            None,
        )

    @property
    def many_returns(self) -> List[DocstringReturns]:
        """Return a list of information on function return."""
        return [item for item in self.meta if isinstance(item, DocstringReturns)]

    @property
    def yields(self) -> Optional[DocstringYields]:
        """Return information on function yield.

        Takes the first generator information.
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
    def many_yields(self) -> List[DocstringYields]:
        """Return a list of information on function yields."""
        return [item for item in self.meta if isinstance(item, DocstringYields)]

    @property
    def deprecation(self) -> Optional[DocstringDeprecated]:
        """Return a single information on function deprecation notes."""
        return next(
            (item for item in self.meta if isinstance(item, DocstringDeprecated)),
            None,
        )

    @property
    def examples(self) -> List[DocstringExample]:
        """Return a list of information on function examples."""
        return [item for item in self.meta if isinstance(item, DocstringExample)]
