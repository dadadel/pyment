"""Unit tests for pymend.file_parser.py."""

import ast

from pymend.file_parser import AstAnalyzer
from pymend.types import FixerSettings, Parameter


class TestAstAnalyzer:
    """Test ast analyzer."""

    def test_handle_class_body(self) -> None:
        """Handle class body parsing."""
        class_definition = '''\
class C:
    def __init__(self):
        self._x = None
        self.test1 = "test"
        self.test2: Optional[int] = None
        self.test1 = "a"
        self.test3 = self.test4 = None
        self.test5, self.test6 = 1, 2

    @property
    def x(self) -> str | None:
        """I'm the 'x' property."""
        return self._x

    @x.setter
    def x(self, value):
        self._x = value

    @staticmethod
    def a(self, a):
        pass

    @classmethod
    def b(self, b):
        pass

    def c(self, c):
        pass
'''
        class_node = ast.parse(class_definition).body[0]
        analyzer = AstAnalyzer(class_definition, settings=FixerSettings())

        attributes, methods = analyzer.handle_class_body(class_node)

        expected_attributes = [
            Parameter("test1", "_type_", None),
            Parameter("test2", "_type_", None),
            Parameter("test3", "_type_", None),
            Parameter("test4", "_type_", None),
            Parameter("test5", "_type_", None),
            Parameter("test6", "_type_", None),
            Parameter("x", "str | None", None),
        ]
        expected_methods = ["c(c)"]
        assert attributes == expected_attributes
        assert methods == expected_methods

    def test_calculate_function_length(self) -> None:
        """Test that nested function statement length is calculated correctly."""
        function_definition = '''\
def test_function():
    """My docstring, dont count"""
    if 1:
        print(a)
        print(b)
    else:
        for i in range(10):
            print(i)
    with test:
        try:
            something()
        except Exception:
            pass
    return None
'''
        func_node = ast.parse(function_definition).body[0]
        analyzer = AstAnalyzer(function_definition, settings=FixerSettings())
        func_docstring = analyzer.handle_function(func_node)
        assert func_docstring.length == 11
