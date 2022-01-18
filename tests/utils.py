import pytest
import textwrap

def assert_docstring(actual, expected):
    """Assert that docstrings are equal

    Args:
      actual:
      expected:

    Returns:

    Raises:

    """
    def cleanup(multiline):
        return "\n".join(
            line.strip() for line in multiline.split("\n")
        )
    actual = cleanup(textwrap.dedent(actual)[3:-3])
    expected = cleanup(textwrap.dedent(expected))
    assert actual == expected

