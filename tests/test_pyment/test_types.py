"""Unit tests for pyment.types."""

from typing import List

import pytest

from pyment.types import Parameter


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
    def test_uniquefy(self, source: List[Parameter], expected: List[Parameter]) -> None:
        """Test that uniquefy removes duplicates and keeps order."""
        assert list(Parameter.uniquefy(source)) == expected
