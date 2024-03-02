"""Parse docstrings as per Sphinx notation."""

from .common import (
    Docstring,
    DocstringDeprecated,
    DocstringExample,
    DocstringMeta,
    DocstringParam,
    DocstringRaises,
    DocstringReturns,
    DocstringStyle,
    DocstringYields,
    ParseError,
    RenderingStyle,
)
from .parser import compose, parse
from .util import combine_docstrings

Style = DocstringStyle  # backwards compatibility

__all__ = [
    "parse",
    "combine_docstrings",
    "compose",
    "ParseError",
    "Docstring",
    "DocstringMeta",
    "DocstringParam",
    "DocstringRaises",
    "DocstringReturns",
    "DocstringYields",
    "DocstringDeprecated",
    "DocstringExample",
    "DocstringStyle",
    "RenderingStyle",
    "Style",
]
