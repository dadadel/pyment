"""Module for parsing input file and walking ast."""

import ast
import re
from typing import List, Optional, overload

from .types import (
    ClassDocstring,
    DefinitionNodes,
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


class AstAnalyzer:
    """Walk ast and extract module, class and function information."""

    def __init__(self, file_content: str) -> None:
        self.file_content = file_content

    def _is_shebang_or_pragma(self, line: str) -> bool:
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

    def _get_docstring_line(self) -> int:
        """Get the line where the docstring should start."""
        shebang_encoding_lines = 2
        return (
            next(
                (
                    index
                    for index, line in enumerate(
                        self.file_content.splitlines()[:shebang_encoding_lines]
                    )
                    if not self._is_shebang_or_pragma(line)
                ),
                2,
            )
            + 1
        )

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
                node.name if isinstance(node, DefinitionNodes) else "Module",
                str(docnode.value),
                (docnode.lineno, docnode.end_lineno),
            )
        return None

    def handle_module(self, module: ast.Module) -> ModuleDocstring:
        """Extract information about module."""
        docstring_info = self.get_docstring_info(module)
        if docstring_info is None:
            docstring_line = self._get_docstring_line()
            return ModuleDocstring("Module", "", (docstring_line, docstring_line))
        return ModuleDocstring(
            docstring_info.name, docstring_info.docstring, docstring_info.lines
        )

    def get_padded_args_defaults(
        self,
        func: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> List[Optional[str]]:
        """Left-Pad the general args defaults to the length of the args."""
        pos_defaults = [
            self.get_expr_as_string(default) for default in func.args.defaults
        ]
        return [None] * (len(func.args.args) - len(pos_defaults)) + pos_defaults

    @overload
    def get_expr_as_string(self, annotation: None) -> None:
        ...

    @overload
    def get_expr_as_string(self, annotation: ast.expr) -> str:
        ...

    def get_expr_as_string(self, annotation: Optional[ast.expr]) -> Optional[str]:
        """Turn an expression ast node into a sensible string.

        Used for default values and annotations.
        """
        return None if annotation is None else ast.unparse(annotation)

    def get_parameters_sig(
        self, func: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> list[Parameter]:
        """Get information about function parameters."""
        arguments: List[Parameter] = []
        pos_defaults = self.get_padded_args_defaults(func)

        pos_only_args = [
            Parameter(arg.arg, self.get_expr_as_string(arg.annotation), None)
            for arg in func.args.posonlyargs
        ]
        arguments += pos_only_args
        general_args = [
            Parameter(arg.arg, self.get_expr_as_string(arg.annotation), default)
            for arg, default in zip(func.args.args, pos_defaults, strict=True)
        ]
        arguments += general_args
        if vararg := func.args.vararg:
            arguments.append(
                Parameter(
                    f"*{vararg.arg}", self.get_expr_as_string(vararg.annotation), None
                )
            )
        kw_only_args = [
            Parameter(
                arg.arg,
                self.get_expr_as_string(arg.annotation),
                self.get_expr_as_string(default),
            )
            for arg, default in zip(
                func.args.kwonlyargs, func.args.kw_defaults, strict=True
            )
        ]
        arguments += kw_only_args
        if kwarg := func.args.kwarg:
            arguments.append(
                Parameter(
                    f"**{kwarg.arg}", self.get_expr_as_string(kwarg.annotation), None
                )
            )
        return arguments

    def get_return_value_sig(
        self, func: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> ReturnValue:
        """Get information about return value from signature."""
        return_node = func.returns
        return ReturnValue(type_name=self.get_expr_as_string(return_node))

    def handle_function_signature(
        self,
        func: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> FunctionSignature:
        """Extract information about the signature of the function."""
        parameters = self.get_parameters_sig(func)
        if parameters and parameters[0].arg_name == "self":
            parameters.pop(0)
        return_value = self.get_return_value_sig(func)
        return FunctionSignature(parameters, return_value)

    def handle_function_docstring(
        self,
        func: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> DocstringInfo:
        """Extract information about the docstring of the function."""
        docstring_info = self.get_docstring_info(func)
        if docstring_info is None:
            if not func.body:
                msg = "Function body was unexpectedly completely empty."
                raise ValueError(msg)
            lines = (func.body[0].lineno, func.body[0].lineno)
            return DocstringInfo(func.name, "", lines)
        return docstring_info

    def handle_function_body(
        self,
        func: ast.FunctionDef | ast.AsyncFunctionDef,
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
                    returns.add(
                        tuple(
                            sorted(
                                value.id
                                for value in node.value.elts
                                # Needed again for type checker
                                if isinstance(value, ast.Name)
                            )
                        )
                    )
            elif isinstance(node, (ast.Yield, ast.YieldFrom)):
                yields_value = True
                if (
                    isinstance(node, ast.Yield)
                    and isinstance(node.value, ast.Tuple)
                    and all(isinstance(value, ast.Name) for value in node.value.elts)
                ):
                    yields.add(
                        tuple(
                            sorted(
                                value.id
                                for value in node.value.elts
                                # Needed again for type checker
                                if isinstance(value, ast.Name)
                            )
                        )
                    )
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

    def handle_function(
        self,
        func: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> FunctionDocstring:
        """Extract information from signature and docstring."""
        signature = self.handle_function_signature(func)
        docstring = self.handle_function_docstring(func)
        body = self.handle_function_body(func)
        return FunctionDocstring(
            docstring.name,
            docstring.docstring,
            docstring.lines,
            signature=signature,
            body=body,
        )

    def handle_class(self, cls: ast.ClassDef) -> ClassDocstring:
        """Extract information about class docstring."""
        docstring_info = self.get_docstring_info(cls)
        if docstring_info is None:
            if not cls.body:
                msg = "Function body was unexpectedly completely empty."
                raise ValueError(msg)
            lines = (cls.body[0].lineno, cls.body[0].lineno)
            return ClassDocstring(cls.name, "", lines)
        return ClassDocstring(
            docstring_info.name, docstring_info.docstring, docstring_info.lines
        )

    def parse_from_ast(
        self,
    ) -> List[ElementDocstring]:
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
        nodes_of_interest: List[ElementDocstring] = []

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
