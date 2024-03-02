"""Unit tests for pymend.types."""

import pytest

from pymend.types import Parameter


class TestParameter:
    """Test the Parameter dataclass."""

    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            (
                [
                    Parameter("3"),
                    Parameter("1"),
                    Parameter("1"),
                    Parameter("4"),
                    Parameter("5"),
                    Parameter("6"),
                    Parameter("6"),
                    Parameter("3"),
                ],
                [
                    Parameter("3"),
                    Parameter("1"),
                    Parameter("4"),
                    Parameter("5"),
                    Parameter("6"),
                ],
            ),
        ],
    )
    def test_uniquefy(self, source: list[Parameter], expected: list[Parameter]) -> None:
        """Test that uniquefy removes duplicates and keeps order."""
        assert list(Parameter.uniquefy(source)) == expected
