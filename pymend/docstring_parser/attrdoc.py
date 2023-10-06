"""Attribute docstrings parsing.

.. seealso:: https://peps.python.org/pep-0257/#what-is-a-docstring
"""

import ast
import inspect
import textwrap
from types import ModuleType
from typing import Any, Optional, Union, overload

from typing_extensions import TypeGuard, override

from .common import Docstring, DocstringParam

ast_constant_attr = {
    ast.Constant: "value",
    # python <= 3.7:
    ast.NameConstant: "value",
    ast.Num: "n",
    ast.Str: "s",
}


def ast_get_constant_value(
    node: Union[ast.Str, ast.Num, ast.NameConstant, ast.Constant]
) -> Any:  # noqa: ANN401
    """Return the constant's value if the given node is a constant."""
    return getattr(node, ast_constant_attr[node.__class__])


@overload
def ast_unparse(node: None) -> None:
    ...


@overload
def ast_unparse(node: ast.AST) -> str:
    ...


def ast_unparse(node: Optional[ast.AST]) -> Optional[str]:
    """Convert the AST node to source code as a string."""
    if node is None:
        return None
    return ast.unparse(node)


def ast_is_literal_str(node: ast.AST) -> TypeGuard[ast.Expr]:
    """Return True if the given node is a literal string."""
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, (ast.Constant, ast.Str))
        and isinstance(ast_get_constant_value(node.value), str)
    )


def ast_get_attribute(
    node: ast.AST,
) -> Optional[tuple[str, Optional[str], Optional[str]]]:
    """Return name, type and default if the given node is an attribute."""
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        target = node.targets[0] if isinstance(node, ast.Assign) else node.target
        if isinstance(target, ast.Name):
            type_str = None
            if isinstance(node, ast.AnnAssign):
                type_str = ast_unparse(node.annotation)
            default = ast_unparse(node.value) if node.value else None
            return target.id, type_str, default
    return None


class AttributeDocstrings(ast.NodeVisitor):
    """An ast.NodeVisitor that collects attribute docstrings."""

    attr_docs = None
    prev_attr = None

    @override
    def visit(self, node: ast.AST) -> None:
        """Visit a node and collect its attribute docstrings."""
        if self.prev_attr and self.attr_docs is not None and ast_is_literal_str(node):
            attr_name, attr_type, attr_default = self.prev_attr
            # This is save because `ast_is_literal_str`
            # ensure that node.value is of type (ast.Constant, ast.Str)
            self.attr_docs[attr_name] = (
                ast_get_constant_value(
                    node.value  # pyright: ignore[reportGeneralTypeIssues]
                ),
                attr_type,
                attr_default,
            )
        self.prev_attr = ast_get_attribute(node)
        if isinstance(node, (ast.ClassDef, ast.Module)):
            self.generic_visit(node)

    def get_attr_docs(
        self, component: Any  # noqa: ANN401
    ) -> dict[str, tuple[str, Optional[str], Optional[str]]]:
        """Get attribute docstrings from the given component.

        Parameters
        ----------
        component : Any
            component to process (class or module)

        Returns
        -------
        Dict[str, Tuple[str, Optional[str], Optional[str]]]
            for each attribute docstring, a tuple with (description,
            type, default)
        """
        self.attr_docs = {}
        self.prev_attr = None
        try:
            source = textwrap.dedent(inspect.getsource(component))
        except OSError:
            pass
        else:
            # This change might cause issues with older python versions
            # Not sure yet.
            tree = ast.parse(source)
            self.visit(tree)
        return self.attr_docs


def add_attribute_docstrings(
    obj: Union[type, ModuleType], docstring: Docstring
) -> None:
    """Add attribute docstrings found in the object's source code.

    Parameters
    ----------
    obj : Union[type, ModuleType]
        object from which to parse attribute docstrings
    docstring : Docstring
        Docstring object where found attributes are added
    """
    params = {p.arg_name for p in docstring.params}
    for arg_name, (description, type_name, default) in (
        AttributeDocstrings().get_attr_docs(obj).items()
    ):
        if arg_name not in params:
            param = DocstringParam(
                args=["attribute", arg_name],
                description=description,
                arg_name=arg_name,
                type_name=type_name,
                is_optional=default is not None,
                default=default,
            )
            docstring.meta.append(param)
