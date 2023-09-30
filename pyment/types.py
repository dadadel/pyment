"""Module for defining commonly used types."""

import ast
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, TypeAlias

Style = Enum("Style", ["UNKNOWN", "GOOGLE", "NUMPY", "GROUP", "JAVADOC", "REST"])


@dataclass
class DocstringInfo:
    """Wrapper around raw docstring."""

    name: str
    docstring: str
    lines: Tuple[int, Optional[int]]

    def parse_docstring(self) -> None:
        """Perform some parsing of the docstring and store the result.

        Default is to do nothing.
        """
        return

    def produce_output_docstring(self, _style: Style = Style.NUMPY) -> str:
        """Produce the output docstring for the element.

        Default is to:
            Add a missing '.' to the first line
            Insert a missing blank line after the first
            Remove trailing blank lines

        Parameters
        ----------
        _style : Style
            The docstring style to use, by default Style.NUMPY

        Returns
        -------
        str
            The optionally reformatted docstring.
        """
        lines = [line.rstrip() for line in self.docstring.splitlines()]
        if not lines:
            return "_summary_."
        if not lines[0].endswith("."):
            lines[0] += "."
        if len(lines) >= 2 and lines[1].strip() != "":
            lines.insert(1, "")
        while lines and lines[-1].strip() == "":
            lines.pop()
        return "\n".join(lines)


@dataclass
class ModuleDocstring(DocstringInfo):
    """Information about a module."""


@dataclass
class ClassDocstring(DocstringInfo):
    """Information about a module."""


@dataclass
class Parameter:
    """Info for parameter from signature."""

    name: str
    type_info: Optional[str]
    default: Optional[str]


@dataclass
class ParameterDoc:
    """Info for parameter from docstring."""

    param: Parameter
    description: str


@dataclass
class ReturnValue:
    """Info about return value from signature."""

    type_info: Optional[str]


@dataclass
class ReturnValueDoc:
    """Info about return value from docstring."""

    type_info: str
    name: Optional[str]
    description: str


@dataclass
class FunctionSignature:
    """Information about a function signature."""

    params: List[Parameter]
    return_value: ReturnValue


@dataclass
class FunctionDocstring(DocstringInfo):
    """Information about a function from docstring."""

    signature: FunctionSignature
    # TODO: other sections


ElementDocstring: TypeAlias = ModuleDocstring | ClassDocstring | FunctionDocstring
DefinitionNodes: TypeAlias = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
NodeOfInterest: TypeAlias = DefinitionNodes | ast.Module
