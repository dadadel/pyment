"""Module for parsing input file and walking ast."""

import ast
import re
from typing import Optional, Union

from .docstring_parser.attrdoc import ast_unparse
from .types import (
    ClassDocstring,
    DocstringInfo,
    ElementDocstring,
    FunctionBody,
    FunctionDocstring,
    FunctionSignature,
    ModuleDocstring,
    NodeOfInterest,
    Parameter,
    ReturnValue,
)

__author__ = "J-E. Nitschke"
__copyright__ = "Copyright 2023-2023"
__licence__ = "GPL3"
__version__ = "1.0.0"
__maintainer__ = "J-E. Nitschke"


class AstAnalyzer:
    """Walk ast and extract module, class and function information."""

    def __init__(self, file_content: str) -> None:
        self.file_content = file_content

    def parse_from_ast(
        self,
    ) -> list[ElementDocstring]:
        """Walk AST of the input file extract info about module, classes and functions.

        For the module and classes and the raw docstring
        and its line numbers are extracted.

        For functions the raw docstring and its line numbers are extracted.
        Additionally the signature is parsed for parameters and return value.

        Returns
        -------
        List[ElementDocstring]
            List of information about module, classes and functions.
        """
        nodes_of_interest: list[ElementDocstring] = []

        for node in ast.walk(ast.parse(self.file_content)):
            if isinstance(node, ast.Module):
                nodes_of_interest.append(self.handle_module(node))
            elif isinstance(node, ast.ClassDef):
                nodes_of_interest.append(self.handle_class(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if any(
                    name.id == "overload"
                    for name in node.decorator_list
                    if isinstance(name, ast.Name)
                ):
                    continue
                nodes_of_interest.append(self.handle_function(node))
        return nodes_of_interest

    def handle_module(self, module: ast.Module) -> ModuleDocstring:
        """Extract information about module."""
        docstring_info = self.get_docstring_info(module)
        if docstring_info is None:
            docstring_line = self._get_docstring_line()
            return ModuleDocstring("Module", "", (docstring_line, docstring_line))
        return ModuleDocstring(
            docstring_info.name, docstring_info.docstring, docstring_info.lines
        )

    def handle_class(self, cls: ast.ClassDef) -> ClassDocstring:
        """Extract information about class docstring."""
        docstring = self.handle_elem_docstring(cls)
        attributes, methods = self.handle_class_body(cls)
        return ClassDocstring(
            docstring.name,
            docstring.docstring,
            docstring.lines,
            attributes=attributes,
            methods=methods,
        )

    def handle_function(
        self,
        func: Union[ast.FunctionDef, ast.AsyncFunctionDef],
    ) -> FunctionDocstring:
        """Extract information from signature and docstring."""
        docstring = self.handle_elem_docstring(func)
        signature = self.handle_function_signature(func)
        body = self.handle_function_body(func)
        return FunctionDocstring(
            docstring.name,
            docstring.docstring,
            docstring.lines,
            signature=signature,
            body=body,
        )

    def handle_elem_docstring(
        self,
        elem: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef],
    ) -> DocstringInfo:
        """Extract information about the docstring of the function."""
        docstring_info = self.get_docstring_info(elem)
        if docstring_info is None:
            if not elem.body:
                msg = "Function body was unexpectedly completely empty."
                raise ValueError(msg)
            lines = (elem.body[0].lineno, elem.body[0].lineno)
            return DocstringInfo(elem.name, "", lines)
        return docstring_info

    def get_docstring_info(self, node: NodeOfInterest) -> Optional[DocstringInfo]:
        """Get docstring and line number if available."""
        if ast.get_docstring(node):
            if not (
                node.body
                and isinstance(first_element := node.body[0], ast.Expr)
                and isinstance(docnode := first_element.value, ast.Constant)
            ):
                msg = (
                    "Expected first entry in body to be the "
                    "docstring, but found nothing or something else."
                )
                raise ValueError(msg)
            return DocstringInfo(
                # Can not use DefinitionNodes in isinstance checks before 3.10
                node.name
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                )
                else "Module",
                str(docnode.value),
                (docnode.lineno, docnode.end_lineno),
            )
        return None

    def _get_docstring_line(self) -> int:
        """Get the line where the docstring should start."""
        shebang_encoding_lines = 2
        for index, line in enumerate(
            self.file_content.splitlines()[:shebang_encoding_lines]
        ):
            if not self.is_shebang_or_pragma(line):
                # List indices start at 0 but file lines are counted from 1
                return index + 1
        return shebang_encoding_lines + 1

    def handle_class_body(self, cls: ast.ClassDef) -> tuple[list[Parameter], list[str]]:
        """Extract attributes and methods from class body.

        Will walk the AST of the ClassDef node and add each function encountered
        as a method.

        If the `__init__` method is encountered walk its body for attribute
        definitions.
        """
        attributes: list[Parameter] = []
        methods: list[str] = []
        for node in cls.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            # Document non-private methods.
            # Exclude some like statismethods and properties
            if not (node.name.startswith("_") or self._has_excluding_decorator(node)):
                methods.append(self._get_method_signature(node))
            # Extract attributes from init method.
            # Excluded from first because of the leading underscore
            elif node.name == "__init__":
                attributes.extend(self._get_attributes_from_init(node))
            elif "property" in {
                decorator.id
                for decorator in node.decorator_list
                if isinstance(decorator, ast.Name)
            }:
                return_value = self.get_return_value_sig(node)
                attributes.append(Parameter(node.name, return_value.type_name, None))
        # Remove duplicates from attributes while maintaining order
        return list(Parameter.uniquefy(attributes)), methods

    def handle_function_signature(
        self,
        func: Union[ast.FunctionDef, ast.AsyncFunctionDef],
    ) -> FunctionSignature:
        """Extract information about the signature of the function."""
        parameters = self.get_parameters_sig(func)
        if parameters and parameters[0].arg_name == "self":
            parameters.pop(0)
        return_value = self.get_return_value_sig(func)
        return FunctionSignature(parameters, return_value)

    def handle_function_body(
        self,
        func: Union[ast.FunctionDef, ast.AsyncFunctionDef],
    ) -> FunctionBody:
        """Check the function body for yields, raises and value returns."""
        returns = set()
        returns_value = False
        yields = set()
        yields_value = False
        raises = []
        for node in ast.walk(func):
            if isinstance(node, ast.Return) and node.value is not None:
                returns_value = True
                if isinstance(node.value, ast.Tuple) and all(
                    isinstance(value, ast.Name) for value in node.value.elts
                ):
                    returns.add(self._get_ids_from_returns(node.value.elts))
            elif isinstance(node, (ast.Yield, ast.YieldFrom)):
                yields_value = True
                if (
                    isinstance(node, ast.Yield)
                    and isinstance(node.value, ast.Tuple)
                    and all(isinstance(value, ast.Name) for value in node.value.elts)
                ):
                    yields.add(self._get_ids_from_returns(node.value.elts))
            elif isinstance(node, ast.Raise):
                if node.exc and isinstance(node.exc, ast.Name):
                    raises.append(node.exc.id)
                else:
                    raises.append("")
        return FunctionBody(
            returns_value=returns_value,
            returns=returns,
            yields_value=yields_value,
            yields=yields,
            raises=raises,
        )

    def get_return_value_sig(
        self, func: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> ReturnValue:
        """Get information about return value from signature."""
        return_node = func.returns
        return ReturnValue(type_name=ast_unparse(return_node))

    def get_parameters_sig(
        self, func: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> list[Parameter]:
        """Get information about function parameters."""
        arguments: list[Parameter] = []
        pos_defaults = self.get_padded_args_defaults(func)

        pos_only_args = [
            Parameter(arg.arg, ast_unparse(arg.annotation), None)
            for arg in func.args.posonlyargs
        ]
        arguments += pos_only_args
        general_args = [
            Parameter(arg.arg, ast_unparse(arg.annotation), default)
            for arg, default in zip(func.args.args, pos_defaults)
        ]
        arguments += general_args
        if vararg := func.args.vararg:
            arguments.append(
                Parameter(f"*{vararg.arg}", ast_unparse(vararg.annotation), None)
            )
        kw_only_args = [
            Parameter(
                arg.arg,
                ast_unparse(arg.annotation),
                ast_unparse(default),
            )
            for arg, default in zip(func.args.kwonlyargs, func.args.kw_defaults)
        ]
        arguments += kw_only_args
        if kwarg := func.args.kwarg:
            arguments.append(
                Parameter(f"**{kwarg.arg}", ast_unparse(kwarg.annotation), None)
            )
        return arguments

    @staticmethod
    def is_shebang_or_pragma(line: str) -> bool:
        """Check if a given line contains encoding or shebang.

        Parameters
        ----------
        line : str
            Line to check

        Returns
        -------
        bool
            Whether the given line contains encoding or shebang
        """
        shebang_regex = r"^#!(.*)"
        if re.search(shebang_regex, line) is not None:
            return True
        pragma_regex = r"^#.*coding[=:]\s*([-\w.]+)"
        return re.search(pragma_regex, line) is not None

    def get_padded_args_defaults(
        self,
        func: Union[ast.FunctionDef, ast.AsyncFunctionDef],
    ) -> list[Optional[str]]:
        """Left-Pad the general args defaults to the length of the args."""
        pos_defaults = [ast_unparse(default) for default in func.args.defaults]
        return [None] * (len(func.args.args) - len(pos_defaults)) + pos_defaults

    def _has_excluding_decorator(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> bool:
        """Exclude function with some decorators.

        Currently excluded:
            staticmethod
            classmethod
            property (and related)
        """
        decorators = node.decorator_list
        excluded_decorators = {"staticmethod", "classmethod", "property"}
        for decorator in decorators:
            if isinstance(decorator, ast.Name) and decorator.id in excluded_decorators:
                return True
            # Handle property related decorators like in
            # @x.setter
            # def x(self, value):
            #     self._x = value  # noqa: ERA001

            # @x.deleter
            # def x(self):
            #     del self._x
            if (
                isinstance(decorator, ast.Attribute)
                and isinstance(decorator.value, ast.Name)
                and decorator.value.id == node.name
            ):
                return True
        return False

    def _get_attributes_from_init(
        self, init: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> list[Parameter]:
        """Iterate over body and grab every assignment `self.abc = XYZ`."""
        attributes: list[Parameter] = []
        for node in init.body:
            if not isinstance(node, ast.Assign):
                continue
            # Targets is a list in case of multiple assignent
            # a = b = 3  # noqa: ERA001
            for target in node.targets:
                if (
                    # We only care about assignments self.abc
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                    # Skip private attributes like self._x
                    and not target.attr.startswith("_")
                ):
                    attributes.append(Parameter(target.attr, "_type_", None))
        return attributes

    def _get_method_signature(
        self, func: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> str:
        """Remove self from signature and return the unparsed string."""
        arguments = func.args
        if arguments.posonlyargs:
            arguments.posonlyargs = [
                arg for arg in arguments.posonlyargs if arg.arg != "self"
            ]
        elif arguments.args:
            arguments.args = [arg for arg in arguments.args if arg.arg != "self"]
        return f"{func.name}({ast.unparse(arguments)})"

    def _get_ids_from_returns(self, values: list[ast.expr]) -> tuple[str, ...]:
        """Get the ids/names for all the expressions in the list."""
        return tuple(
            value.id
            for value in values
            # Needed again for type checker
            if isinstance(value, ast.Name)
        )
