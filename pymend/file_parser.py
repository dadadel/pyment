"""Module for parsing input file and walking ast."""

import ast
import re
from typing import Optional, Union

from typing_extensions import TypeGuard

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
        """Initialize the Analyzer with the file contents.

        The only reason this is a class is to have the raw
        file_contents available at any point of the analysis to double check
        something. Currently used for the module docstring and docstring
        modifiers.

        Parameters
        ----------
        file_content : str
            File contents to store.
        """
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
        list[ElementDocstring]
            List of information about module, classes and functions.

        Raises
        ------
        AssertionError
            If the source file content could not be parsed into an ast.
        """
        nodes_of_interest: list[ElementDocstring] = []
        try:
            file_ast = ast.parse(self.file_content)
        except Exception as exc:  # noqa: BLE001
            msg = f"Failed to parse source file AST: {exc}\n"
            raise AssertionError(msg) from exc
        for node in ast.walk(file_ast):
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
        """Extract information about module.

        Parameters
        ----------
        module : ast.Module
            Node representing the full module.

        Returns
        -------
        ModuleDocstring
            Docstring representation for the module.
        """
        docstring_info = self.get_docstring_info(module)
        if docstring_info is None:
            docstring_line = self._get_docstring_line()
            return ModuleDocstring(
                "Module",
                docstring="",
                lines=(docstring_line, docstring_line),
                modifier="",
            )
        return ModuleDocstring(
            docstring_info.name,
            docstring_info.docstring,
            docstring_info.lines,
            docstring_info.modifier,
        )

    def handle_class(self, cls: ast.ClassDef) -> ClassDocstring:
        """Extract information about class docstring.

        Parameters
        ----------
        cls : ast.ClassDef
            Node representing a class definition.

        Returns
        -------
        ClassDocstring
            Docstring representation for a class.
        """
        docstring = self.handle_elem_docstring(cls)
        attributes, methods = self.handle_class_body(cls)
        return ClassDocstring(
            docstring.name,
            docstring.docstring,
            docstring.lines,
            docstring.modifier,
            attributes=attributes,
            methods=methods,
        )

    def handle_function(
        self,
        func: Union[ast.FunctionDef, ast.AsyncFunctionDef],
    ) -> FunctionDocstring:
        """Extract information from signature and docstring.

        Parameters
        ----------
        func : Union[ast.FunctionDef, ast.AsyncFunctionDef]
            Node representing a function definition.

        Returns
        -------
        FunctionDocstring
            Docstring representation of a function.
        """
        docstring = self.handle_elem_docstring(func)
        signature = self.handle_function_signature(func)
        body = self.handle_function_body(func)
        return FunctionDocstring(
            docstring.name,
            docstring.docstring,
            docstring.lines,
            docstring.modifier,
            signature=signature,
            body=body,
        )

    def handle_elem_docstring(
        self,
        elem: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef],
    ) -> DocstringInfo:
        """Extract information about the docstring of the function.

        Parameters
        ----------
        elem : Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]
            Element representing a function or class definition.

        Returns
        -------
        DocstringInfo
            Return general information about the docstring of the element.

        Raises
        ------
        ValueError
            If the element did not have a body at all. This should not happen
            for valid functions or classes.
        """
        docstring_info = self.get_docstring_info(elem)
        if docstring_info is None:
            if not elem.body:
                msg = "Function body was unexpectedly completely empty."
                raise ValueError(msg)
            lines = (elem.body[0].lineno, elem.body[0].lineno)
            return DocstringInfo(name=elem.name, docstring="", lines=lines, modifier="")
        return docstring_info

    def get_docstring_info(self, node: NodeOfInterest) -> Optional[DocstringInfo]:
        """Get docstring and line number if available.

        Parameters
        ----------
        node : NodeOfInterest
            Get general information about the docstring of any node
            if interest.

        Returns
        -------
        Optional[DocstringInfo]
            Information about the docstring if the element contains one.
            Or `None` if there was no docstring at all.

        Raises
        ------
        ValueError
            If the first element of the body is not a docstring after
            `ast.get_docstring()` returned one.
        """
        if ast.get_docstring(node):
            if not (
                node.body
                and isinstance(first_element := node.body[0], ast.Expr)
                and isinstance(docnode := first_element.value, ast.Constant)
                and isinstance(docnode.value, str)
            ):
                msg = (
                    "Expected first entry in body to be the "
                    "docstring, but found nothing or something else."
                )
                raise ValueError(msg)
            modifier = self._get_modifier(
                self.file_content.splitlines()[docnode.lineno - 1]
            )
            return DocstringInfo(
                # Can not use DefinitionNodes in isinstance checks before 3.10
                node.name
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                )
                else "Module",
                str(docnode.value),
                (docnode.lineno, docnode.end_lineno),
                modifier,
            )
        return None

    def _get_modifier(self, line: str) -> str:
        """Get the string modifier from the start of a docstring.

        Parameters
        ----------
        line : str
            Line to check

        Returns
        -------
        str
            Modifier(s) of the string.
        """
        line = line.strip()
        delimiters = ['"""', "'''"]
        modifiers = ["r", "u", "f"]
        if not line:
            return ""
        if line[:3] in delimiters:
            return ""
        if line[0] in modifiers and line[1:4] in delimiters:
            return line[0]
        if line[0] in modifiers and line[1] in modifiers and line[2:5] in delimiters:
            return line[:2]
        return ""

    def _get_docstring_line(self) -> int:
        """Get the line where the module docstring should start.

        Returns
        -------
        int
            Starting line (starts at 1) of the docstring.
        """
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

        Parameters
        ----------
        cls : ast.ClassDef
            Node representing a class definition.

        Returns
        -------
        attributes : list[Parameter]
            List of the parameters that make up the classes attributes.
        methods : list[str]
            List of the method names in the class.
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
        """Extract information about the signature of the function.

        Parameters
        ----------
        func : Union[ast.FunctionDef, ast.AsyncFunctionDef]
            Node representing a function definition

        Returns
        -------
        FunctionSignature
            Information extracted from the function signature
        """
        parameters = self.get_parameters_sig(func)
        if parameters and parameters[0].arg_name == "self":
            parameters.pop(0)
        return_value = self.get_return_value_sig(func)
        return FunctionSignature(parameters, return_value)

    def handle_function_body(
        self,
        func: Union[ast.FunctionDef, ast.AsyncFunctionDef],
    ) -> FunctionBody:
        """Check the function body for yields, raises and value returns.

        Parameters
        ----------
        func : Union[ast.FunctionDef, ast.AsyncFunctionDef]
            Node representing a function definition

        Returns
        -------
        FunctionBody
            Information extracted from the function body.
        """
        returns: set[tuple[str, ...]] = set()
        returns_value = False
        yields: set[tuple[str, ...]] = set()
        yields_value = False
        raises: list[str] = []
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
                pascal_case_regex = r"^(?:[A-Z][a-z]+)+$"
                if not node.exc:
                    raises.append("")
                elif isinstance(node.exc, ast.Name) and re.match(
                    pascal_case_regex, node.exc.id
                ):
                    raises.append(node.exc.id)
                elif (
                    isinstance(node.exc, ast.Call)
                    and isinstance(node.exc.func, ast.Name)
                    and re.match(pascal_case_regex, node.exc.func.id)
                ):
                    raises.append(node.exc.func.id)
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
        """Get information about return value from signature.

        Parameters
        ----------
        func : Union[ast.FunctionDef, ast.AsyncFunctionDef]
            Node representing a function definition

        Returns
        -------
        ReturnValue
            Return information extracted from the function signature.
        """
        return ReturnValue(type_name=ast_unparse(func.returns))

    def get_parameters_sig(
        self, func: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> list[Parameter]:
        """Get information about function parameters.

        Parameters
        ----------
        func : Union[ast.FunctionDef, ast.AsyncFunctionDef]
            Node representing a function definition

        Returns
        -------
        list[Parameter]
            Parameter information from the function signature.
        """
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
        # Filter out unused arguments.
        return [
            argument for argument in arguments if not argument.arg_name.startswith("_")
        ]

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
        """Left-Pad the general args defaults to the length of the args.

        Parameters
        ----------
        func : Union[ast.FunctionDef, ast.AsyncFunctionDef]
            Node representing a function definition

        Returns
        -------
        list[Optional[str]]
            Left padded (with `None`) list of function arguments.
        """
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

        Parameters
        ----------
        node : Union[ast.FunctionDef, ast.AsyncFunctionDef]
            Node representing a function definition

        Returns
        -------
        bool
            Whether the function as any decorators that exclude it from
            being recognized as a standard method.
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

    def _check_if_node_is_self_attributes(
        self, node: ast.expr
    ) -> TypeGuard[ast.Attribute]:
        """Check whether the node represents a public attribute of self (self.abc).

        Parameters
        ----------
        node : ast.expr
            Node representing the expression to be checked.

        Returns
        -------
        TypeGuard[ast.Attribute]
            True if the node represents a public attribute of self.
        """
        return (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "self"
            and not node.attr.startswith("_")
        )

    def _check_and_handle_assign_node(
        self, target: ast.expr, attributes: list[Parameter]
    ) -> None:
        """Check if the assignment node contains assignments to self.X.

        Add it to the list of attributes if that is the case.

        Parameters
        ----------
        target : ast.expr
            Node representing an assignment
        attributes : list[Parameter]
            List of attributes the node attribute should be added to.
        """
        if isinstance(target, (ast.Tuple, ast.List)):
            for node in target.elts:
                if self._check_if_node_is_self_attributes(node):
                    attributes.append(Parameter(node.attr, "_type_", None))
        elif self._check_if_node_is_self_attributes(target):
            attributes.append(Parameter(target.attr, "_type_", None))

    def _get_attributes_from_init(
        self, init: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> list[Parameter]:
        """Iterate over body and grab every assignment `self.abc = XYZ`.

        Parameters
        ----------
        init : Union[ast.FunctionDef, ast.AsyncFunctionDef]
            _description_

        Returns
        -------
        list[Parameter]
            _description_
        """
        attributes: list[Parameter] = []
        for node in init.body:
            if isinstance(node, ast.Assign):
                # Targets is a list in case of multiple assignent
                # a = b = 3  # noqa: ERA001
                for target in node.targets:
                    self._check_and_handle_assign_node(target, attributes)
            # Also handle annotated assignments
            # c: int = "Test"  # noqa: ERA001
            elif isinstance(node, ast.AnnAssign):
                self._check_and_handle_assign_node(node.target, attributes)
        return attributes

    def _get_method_signature(
        self, func: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> str:
        """Remove self from signature and return the unparsed string.

        Parameters
        ----------
        func : Union[ast.FunctionDef, ast.AsyncFunctionDef]
            Node representing a function definition.

        Returns
        -------
        str
            String of the method signature with `self` removed.
        """
        arguments = func.args
        if arguments.posonlyargs:
            arguments.posonlyargs = [
                arg for arg in arguments.posonlyargs if arg.arg != "self"
            ]
        elif arguments.args:
            arguments.args = [arg for arg in arguments.args if arg.arg != "self"]
        return f"{func.name}({ast.unparse(arguments)})"

    def _get_ids_from_returns(self, values: list[ast.expr]) -> tuple[str, ...]:
        """Get the ids/names for all the expressions in the list.

        Parameters
        ----------
        values : list[ast.expr]
            List of expressions to extract the ids from.

        Returns
        -------
        tuple[str, ...]
            Tuple of ids of the original expressions.
        """
        return tuple(
            value.id
            for value in values
            # Needed again for type checker
            if isinstance(value, ast.Name)
        )
