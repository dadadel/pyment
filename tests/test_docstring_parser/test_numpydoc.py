"""Tests for numpydoc-style docstring routines."""
from typing import List, Optional, Tuple

import pytest

from pyment.docstring_parser.numpydoc import compose, parse


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("", None),
        ("\n", None),
        ("Short description", "Short description"),
        ("\nShort description\n", "Short description"),
        ("\n   Short description\n", "Short description"),
    ],
)
def test_short_description(source: str, expected: str) -> None:
    """Test parsing short description."""
    docstring = parse(source)
    assert docstring.short_description == expected
    assert docstring.long_description is None
    assert not docstring.meta


@pytest.mark.parametrize(
    ("source", "expected_short_desc", "expected_long_desc", "expected_blank"),
    [
        (
            "Short description\n\nLong description",
            "Short description",
            "Long description",
            True,
        ),
        (
            """
            Short description

            Long description
            """,
            "Short description",
            "Long description",
            True,
        ),
        (
            """
            Short description

            Long description
            Second line
            """,
            "Short description",
            "Long description\nSecond line",
            True,
        ),
        (
            "Short description\nLong description",
            "Short description",
            "Long description",
            False,
        ),
        (
            """
            Short description
            Long description
            """,
            "Short description",
            "Long description",
            False,
        ),
        (
            "\nShort description\nLong description\n",
            "Short description",
            "Long description",
            False,
        ),
        (
            """
            Short description
            Long description
            Second line
            """,
            "Short description",
            "Long description\nSecond line",
            False,
        ),
    ],
)
def test_long_description(
    source: str,
    expected_short_desc: str,
    expected_long_desc: str,
    *,
    expected_blank: bool,
) -> None:
    """Test parsing long description."""
    docstring = parse(source)
    assert docstring.short_description == expected_short_desc
    assert docstring.long_description == expected_long_desc
    assert docstring.blank_after_short_description == expected_blank
    assert not docstring.meta


@pytest.mark.parametrize(
    (
        "source",
        "expected_short_desc",
        "expected_long_desc",
        "expected_blank_short_desc",
        "expected_blank_long_desc",
    ),
    [
        (
            """
            Short description
            Parameters
            ----------
            asd
            """,
            "Short description",
            None,
            False,
            False,
        ),
        (
            """
            Short description
            Long description
            Parameters
            ----------
            asd
            """,
            "Short description",
            "Long description",
            False,
            False,
        ),
        (
            """
            Short description
            First line
                Second line
            Parameters
            ----------
            asd
            """,
            "Short description",
            "First line\n    Second line",
            False,
            False,
        ),
        (
            """
            Short description

            First line
                Second line
            Parameters
            ----------
            asd
            """,
            "Short description",
            "First line\n    Second line",
            True,
            False,
        ),
        (
            """
            Short description

            First line
                Second line

            Parameters
            ----------
            asd
            """,
            "Short description",
            "First line\n    Second line",
            True,
            True,
        ),
        (
            """
            Parameters
            ----------
            asd
            """,
            None,
            None,
            False,
            False,
        ),
    ],
)
def test_meta_newlines(
    source: str,
    expected_short_desc: Optional[str],
    expected_long_desc: Optional[str],
    *,
    expected_blank_short_desc: bool,
    expected_blank_long_desc: bool,
) -> None:
    """Test parsing newlines around description sections."""
    docstring = parse(source)
    assert docstring.short_description == expected_short_desc
    assert docstring.long_description == expected_long_desc
    assert docstring.blank_after_short_description == expected_blank_short_desc
    assert docstring.blank_after_long_description == expected_blank_long_desc
    assert len(docstring.meta) == 1


def test_meta_with_multiline_description() -> None:
    """Test parsing multiline meta documentation."""
    docstring = parse(
        """
        Short description

        Parameters
        ----------
        spam
            asd
            1
                2
            3
        """
    )
    assert docstring.short_description == "Short description"
    assert len(docstring.meta) == 1
    assert docstring.meta[0].args == ["param", "spam"]
    assert docstring.meta[0].arg_name == "spam"
    assert docstring.meta[0].description == "asd\n1\n    2\n3"


@pytest.mark.parametrize(
    ("source", "expected_is_optional", "expected_type_name", "expected_default"),
    [
        (
            """
                Parameters
                ----------
                arg1 : int
                    The first arg
                """,
            False,
            "int",
            None,
        ),
        (
            """
                Parameters
                ----------
                arg2 : str
                    The second arg
                """,
            False,
            "str",
            None,
        ),
        (
            """
                Parameters
                ----------
                arg3 : float, optional
                    The third arg. Default is 1.0.
                """,
            True,
            "float",
            "1.0",
        ),
        (
            """
                Parameters
                ----------
                arg4 : Optional[Dict[str, Any]], optional
                    The fourth arg. Defaults to None
                """,
            True,
            "Optional[Dict[str, Any]]",
            "None",
        ),
        (
            """
                Parameters
                ----------
                arg5 : str, optional
                    The fifth arg. Default: DEFAULT_ARGS
                """,
            True,
            "str",
            "DEFAULT_ARGS",
        ),
        (
            """
                Parameters
                ----------
                parameter_without_default : int
                    The parameter_without_default is required.
                """,
            False,
            "int",
            None,
        ),
    ],
)
def test_default_args(
    source: str,
    *,
    expected_is_optional: bool,
    expected_type_name: Optional[str],
    expected_default: Optional[str],
) -> None:
    """Test parsing default arguments."""
    docstring = parse(source)
    assert docstring is not None
    assert len(docstring.params) == 1

    arg1 = docstring.params[0]
    assert arg1.is_optional == expected_is_optional
    assert arg1.type_name == expected_type_name
    assert arg1.default == expected_default


def test_multiple_meta() -> None:
    """Test parsing multiple meta."""
    docstring = parse(
        """
        Short description

        Parameters
        ----------
        spam
            asd
            1
                2
            3

        Raises
        ------
        bla
            herp
        yay
            derp
        """
    )
    assert docstring.short_description == "Short description"
    assert len(docstring.meta) == 3
    assert docstring.meta[0].args == ["param", "spam"]
    assert docstring.meta[0].arg_name == "spam"
    assert docstring.meta[0].description == "asd\n1\n    2\n3"
    assert docstring.meta[1].args == ["raises", "bla"]
    assert docstring.meta[1].type_name == "bla"
    assert docstring.meta[1].description == "herp"
    assert docstring.meta[2].args == ["raises", "yay"]
    assert docstring.meta[2].type_name == "yay"
    assert docstring.meta[2].description == "derp"


def test_params() -> None:
    """Test parsing params."""
    docstring = parse("Short description")
    assert len(docstring.params) == 0

    docstring = parse(
        """
        Short description

        Parameters
        ----------
        name
            description 1
        priority : int
            description 2
        sender : str, optional
            description 3
        ratio : Optional[float], optional
            description 4
        """
    )
    assert len(docstring.params) == 4
    assert docstring.params[0].arg_name == "name"
    assert docstring.params[0].type_name is None
    assert docstring.params[0].description == "description 1"
    assert not docstring.params[0].is_optional
    assert docstring.params[1].arg_name == "priority"
    assert docstring.params[1].type_name == "int"
    assert docstring.params[1].description == "description 2"
    assert not docstring.params[1].is_optional
    assert docstring.params[2].arg_name == "sender"
    assert docstring.params[2].type_name == "str"
    assert docstring.params[2].description == "description 3"
    assert docstring.params[2].is_optional
    assert docstring.params[3].arg_name == "ratio"
    assert docstring.params[3].type_name == "Optional[float]"
    assert docstring.params[3].description == "description 4"
    assert docstring.params[3].is_optional

    docstring = parse(
        """
        Short description

        Parameters
        ----------
        name
            description 1
            with multi-line text
        priority : int
            description 2
        """
    )
    assert len(docstring.params) == 2
    assert docstring.params[0].arg_name == "name"
    assert docstring.params[0].type_name is None
    assert docstring.params[0].description == ("description 1\nwith multi-line text")
    assert docstring.params[1].arg_name == "priority"
    assert docstring.params[1].type_name == "int"
    assert docstring.params[1].description == "description 2"


def test_attributes() -> None:
    """Test parsing attributes."""
    docstring = parse("Short description")
    assert len(docstring.params) == 0

    docstring = parse(
        """
        Short description

        Attributes
        ----------
        name
            description 1
        priority : int
            description 2
        sender : str, optional
            description 3
        ratio : Optional[float], optional
            description 4
        """
    )
    assert len(docstring.params) == 4
    assert docstring.params[0].arg_name == "name"
    assert docstring.params[0].type_name is None
    assert docstring.params[0].description == "description 1"
    assert not docstring.params[0].is_optional
    assert docstring.params[1].arg_name == "priority"
    assert docstring.params[1].type_name == "int"
    assert docstring.params[1].description == "description 2"
    assert not docstring.params[1].is_optional
    assert docstring.params[2].arg_name == "sender"
    assert docstring.params[2].type_name == "str"
    assert docstring.params[2].description == "description 3"
    assert docstring.params[2].is_optional
    assert docstring.params[3].arg_name == "ratio"
    assert docstring.params[3].type_name == "Optional[float]"
    assert docstring.params[3].description == "description 4"
    assert docstring.params[3].is_optional

    docstring = parse(
        """
        Short description

        Attributes
        ----------
        name
            description 1
            with multi-line text
        priority : int
            description 2
        """
    )
    assert len(docstring.params) == 2
    assert docstring.params[0].arg_name == "name"
    assert docstring.params[0].type_name is None
    assert docstring.params[0].description == ("description 1\nwith multi-line text")
    assert docstring.params[1].arg_name == "priority"
    assert docstring.params[1].type_name == "int"
    assert docstring.params[1].description == "description 2"


def test_other_params() -> None:
    """Test parsing other parameters."""
    docstring = parse(
        """
        Short description
        Other Parameters
        ----------------
        only_seldom_used_keywords : type, optional
            Explanation
        common_parameters_listed_above : type, optional
            Explanation
        """
    )
    assert len(docstring.meta) == 2
    assert docstring.meta[0].args == [
        "other_param",
        "only_seldom_used_keywords",
    ]
    assert docstring.meta[0].arg_name == "only_seldom_used_keywords"
    assert docstring.meta[0].type_name == "type"
    assert docstring.meta[0].is_optional
    assert docstring.meta[0].description == "Explanation"

    assert docstring.meta[1].args == [
        "other_param",
        "common_parameters_listed_above",
    ]


def test_yields() -> None:
    """Test parsing yields."""
    docstring = parse(
        """
        Short description
        Yields
        ------
        int
            description
        """
    )
    assert len(docstring.meta) == 1
    assert docstring.meta[0].args == ["yields"]
    assert docstring.meta[0].type_name == "int"
    assert docstring.meta[0].description == "description"
    assert docstring.meta[0].yield_name is None
    assert docstring.meta[0].is_generator

    docstring = parse(
        """
        Short description
        Yields
        ------
        int
            description
        str
            another
        """
    )
    assert len(docstring.meta) == 2
    assert docstring.meta[0].args == ["yields"]
    assert docstring.meta[0].type_name == "int"
    assert docstring.meta[0].description == "description"
    assert docstring.meta[0].yield_name is None
    assert docstring.meta[0].is_generator
    assert docstring.meta[1].args == ["yields"]
    assert docstring.meta[1].type_name == "str"
    assert docstring.meta[1].description == "another"
    assert docstring.meta[1].yield_name is None
    assert docstring.meta[1].is_generator
    assert len(docstring.many_yields) == 2
    assert docstring.many_yields[0].type_name == "int"
    assert docstring.many_yields[0].description == "description"
    assert docstring.many_yields[1].type_name == "str"
    assert docstring.many_yields[1].description == "another"


def test_returns() -> None:
    """Test parsing returns."""
    docstring = parse(
        """
        Short description
        """
    )
    assert docstring.returns is None
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 0

    docstring = parse(
        """
        Short description
        Returns
        -------
        type
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name == "type"
    assert docstring.returns.description is None
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 1
    assert docstring.many_returns[0] == docstring.returns

    docstring = parse(
        """
        Short description
        Returns
        -------
        int
            description
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name == "int"
    assert docstring.returns.description == "description"
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 1
    assert docstring.many_returns[0] == docstring.returns

    docstring = parse(
        """
        Returns
        -------
        Optional[Mapping[str, List[int]]]
            A description: with a colon
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name == "Optional[Mapping[str, List[int]]]"
    assert docstring.returns.description == "A description: with a colon"
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 1
    assert docstring.many_returns[0] == docstring.returns

    docstring = parse(
        """
        Short description
        Returns
        -------
        int
            description
            with much text

            even some spacing
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name == "int"
    assert docstring.returns.description == (
        "description\nwith much text\n\neven some spacing"
    )
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 1
    assert docstring.many_returns[0] == docstring.returns

    docstring = parse(
        """
        Short description
        Returns
        -------
        a : int
            description for a
        b : str
            description for b
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name == "int"
    assert docstring.returns.description == ("description for a")
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 2
    assert docstring.many_returns[0].type_name == "int"
    assert docstring.many_returns[0].description == "description for a"
    assert docstring.many_returns[0].return_name == "a"
    assert docstring.many_returns[1].type_name == "str"
    assert docstring.many_returns[1].description == "description for b"
    assert docstring.many_returns[1].return_name == "b"


def test_raises() -> None:
    """Test parsing raises."""
    docstring = parse(
        """
        Short description
        """
    )
    assert len(docstring.raises) == 0

    docstring = parse(
        """
        Short description
        Raises
        ------
        ValueError
            description
        """
    )
    assert len(docstring.raises) == 1
    assert docstring.raises[0].type_name == "ValueError"
    assert docstring.raises[0].description == "description"


def test_warns() -> None:
    """Test parsing warns."""
    docstring = parse(
        """
        Short description
        Warns
        -----
        UserWarning
            description
        """
    )
    assert len(docstring.meta) == 1
    assert docstring.meta[0].type_name == "UserWarning"
    assert docstring.meta[0].description == "description"


def test_simple_sections() -> None:
    """Test parsing simple sections."""
    docstring = parse(
        """
        Short description

        See Also
        --------
        something : some thing you can also see
        actually, anything can go in this section

        Warnings
        --------
        Here be dragons

        Notes
        -----
        None of this is real

        References
        ----------
        Cite the relevant literature, e.g. [1]_.  You may also cite these
        references in the notes section above.

        .. [1] O. McNoleg, "The integration of GIS, remote sensing,
           expert systems and adaptive co-kriging for environmental habitat
           modelling of the Highland Haggis using object-oriented, fuzzy-logic
           and neural-network techniques," Computers & Geosciences, vol. 22,
           pp. 585-588, 1996.
        """
    )
    assert len(docstring.meta) == 4
    assert docstring.meta[0].args == ["see_also"]
    assert docstring.meta[0].description == (
        "something : some thing you can also see\n"
        "actually, anything can go in this section"
    )

    assert docstring.meta[1].args == ["warnings"]
    assert docstring.meta[1].description == "Here be dragons"

    assert docstring.meta[2].args == ["notes"]
    assert docstring.meta[2].description == "None of this is real"

    assert docstring.meta[3].args == ["references"]


@pytest.mark.parametrize(
    ("source", "expected_results"),
    [
        (
            "Description\nExamples\n--------\nlong example\n\nmore here",
            [
                (None, "long example\n\nmore here"),
            ],
        ),
        (
            "Description\nExamples\n--------\n>>> test",
            [
                (">>> test", ""),
            ],
        ),
        (
            "Description\nExamples\n--------\n>>> testa\n>>> testb",
            [
                (">>> testa\n>>> testb", ""),
            ],
        ),
        (
            "Description\nExamples\n--------\n>>> test1\ndesc1",
            [
                (">>> test1", "desc1"),
            ],
        ),
        (
            "Description\nExamples\n--------\n"
            ">>> test1a\n>>> test1b\ndesc1a\ndesc1b",
            [
                (">>> test1a\n>>> test1b", "desc1a\ndesc1b"),
            ],
        ),
        (
            "Description\nExamples\n--------\n>>> test1\ndesc1\n>>> test2\ndesc2",
            [
                (">>> test1", "desc1"),
                (">>> test2", "desc2"),
            ],
        ),
        (
            "Description\nExamples\n--------\n"
            ">>> test1a\n>>> test1b\ndesc1a\ndesc1b\n"
            ">>> test2a\n>>> test2b\ndesc2a\ndesc2b\n",
            [
                (">>> test1a\n>>> test1b", "desc1a\ndesc1b"),
                (">>> test2a\n>>> test2b", "desc2a\ndesc2b"),
            ],
        ),
        (
            "Description\nExamples\n--------\n"
            "    >>> test1a\n    >>> test1b\n    desc1a\n    desc1b\n"
            "    >>> test2a\n    >>> test2b\n    desc2a\n    desc2b\n",
            [
                (">>> test1a\n>>> test1b", "desc1a\ndesc1b"),
                (">>> test2a\n>>> test2b", "desc2a\ndesc2b"),
            ],
        ),
    ],
)
def test_examples(
    source: str, expected_results: List[Tuple[Optional[str], str]]
) -> None:
    """Test parsing examples."""
    docstring = parse(source)
    assert len(docstring.meta) == len(expected_results)
    for meta, expected_result in zip(docstring.meta, expected_results):
        assert meta.description == expected_result[1]
    assert len(docstring.examples) == len(expected_results)
    for example, expected_result in zip(docstring.examples, expected_results):
        assert example.snippet == expected_result[0]
        assert example.description == expected_result[1]


@pytest.mark.parametrize(
    ("source", "expected_depr_version", "expected_depr_desc"),
    [
        (
            "Short description\n\n.. deprecated:: 1.6.0\n    This is busted!",
            "1.6.0",
            "This is busted!",
        ),
        (
            (
                "Short description\n\n"
                ".. deprecated:: 1.6.0\n"
                "    This description has\n"
                "    multiple lines!"
            ),
            "1.6.0",
            "This description has\nmultiple lines!",
        ),
        ("Short description\n\n.. deprecated:: 1.6.0", "1.6.0", None),
        (
            "Short description\n\n.. deprecated::\n    No version!",
            None,
            "No version!",
        ),
        (
            "Short description\n\n.. deprecated::",
            None,
            None,
        ),
    ],
)
def test_deprecation(
    source: str,
    expected_depr_version: Optional[str],
    expected_depr_desc: Optional[str],
) -> None:
    """Test parsing deprecation notes."""
    docstring = parse(source)

    assert docstring.deprecation is not None
    assert docstring.deprecation.version == expected_depr_version
    assert docstring.deprecation.description == expected_depr_desc


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("", ""),
        ("\n", ""),
        ("Short description", "Short description"),
        ("\nShort description\n", "Short description"),
        ("\n   Short description\n", "Short description"),
        (
            "Short description\n\nLong description",
            "Short description\n\nLong description",
        ),
        (
            """
            Short description

            Long description
            """,
            "Short description\n\nLong description",
        ),
        (
            """
            Short description

            Long description
            Second line
            """,
            "Short description\n\nLong description\nSecond line",
        ),
        (
            "Short description\nLong description",
            "Short description\nLong description",
        ),
        (
            """
            Short description
            Long description
            """,
            "Short description\nLong description",
        ),
        (
            "\nShort description\nLong description\n",
            "Short description\nLong description",
        ),
        (
            """
            Short description
            Long description
            Second line
            """,
            "Short description\nLong description\nSecond line",
        ),
        (
            """
            Short description
            Meta:
            -----
                asd
            """,
            "Short description\nMeta:\n-----\n    asd",
        ),
        (
            """
            Short description
            Long description
            Meta:
            -----
                asd
            """,
            "Short description\nLong description\nMeta:\n-----\n    asd",
        ),
        (
            """
            Short description
            First line
                Second line
            Meta:
            -----
                asd
            """,
            "Short description\n"
            "First line\n"
            "    Second line\n"
            "Meta:\n"
            "-----\n"
            "    asd",
        ),
        (
            """
            Short description

            First line
                Second line
            Meta:
            -----
                asd
            """,
            "Short description\n"
            "\n"
            "First line\n"
            "    Second line\n"
            "Meta:\n"
            "-----\n"
            "    asd",
        ),
        (
            """
            Short description

            First line
                Second line

            Meta:
            -----
                asd
            """,
            "Short description\n"
            "\n"
            "First line\n"
            "    Second line\n"
            "\n"
            "Meta:\n"
            "-----\n"
            "    asd",
        ),
        (
            """
            Short description

            Meta:
            -----
                asd
                    1
                        2
                    3
            """,
            "Short description\n"
            "\n"
            "Meta:\n"
            "-----\n"
            "    asd\n"
            "        1\n"
            "            2\n"
            "        3",
        ),
        (
            """
            Short description

            Meta1:
            ------
                asd
                1
                    2
                3
            Meta2:
            ------
                herp
            Meta3:
            ------
                derp
            """,
            "Short description\n"
            "\n"
            "Meta1:\n"
            "------\n"
            "    asd\n"
            "    1\n"
            "        2\n"
            "    3\n"
            "Meta2:\n"
            "------\n"
            "    herp\n"
            "Meta3:\n"
            "------\n"
            "    derp",
        ),
        (
            """
            Short description

            Parameters:
            -----------
                name
                    description 1
                priority: int
                    description 2
                sender: str, optional
                    description 3
                message: str, optional
                    description 4, defaults to 'hello'
                multiline: str, optional
                    long description 5,
                        defaults to 'bye'
            """,
            "Short description\n"
            "\n"
            "Parameters:\n"
            "-----------\n"
            "    name\n"
            "        description 1\n"
            "    priority: int\n"
            "        description 2\n"
            "    sender: str, optional\n"
            "        description 3\n"
            "    message: str, optional\n"
            "        description 4, defaults to 'hello'\n"
            "    multiline: str, optional\n"
            "        long description 5,\n"
            "            defaults to 'bye'",
        ),
        (
            """
            Short description
            Raises:
            -------
                ValueError
                    description
            """,
            "Short description\n"
            "Raises:\n"
            "-------\n"
            "    ValueError\n"
            "        description",
        ),
        (
            """
            Description
            Examples:
            --------
            >>> test1a
            >>> test1b
            desc1a
            desc1b
            >>> test2a
            >>> test2b
            desc2a
            desc2b
            """,
            "Description\n"
            "Examples:\n"
            "--------\n"
            ">>> test1a\n"
            ">>> test1b\n"
            "desc1a\n"
            "desc1b\n"
            ">>> test2a\n"
            ">>> test2b\n"
            "desc2a\n"
            "desc2b",
        ),
    ],
)
def test_compose(source: str, expected: str) -> None:
    """Test compose in default mode."""
    assert compose(parse(source)) == expected
