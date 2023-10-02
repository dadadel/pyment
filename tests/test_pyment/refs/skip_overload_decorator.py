"""_summary_."""
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
