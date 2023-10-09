"""Numpydoc-style docstring parsing.

See
---
https://numpydoc.readthedocs.io/en/latest/format.html
"""

import inspect
import itertools
import re
from collections.abc import Iterable, Iterator
from textwrap import dedent
from typing import Optional, TypeVar

from typing_extensions import override

from .common import (
    Docstring,
    DocstringDeprecated,
    DocstringExample,
    DocstringMeta,
    DocstringParam,
    DocstringRaises,
    DocstringReturns,
    DocstringStyle,
    DocstringYields,
    MainSections,
    ParseError,
    RenderingStyle,
    clean_str,
    split_description,
)

_T = TypeVar("_T")


def _pairwise(
    iterable: Iterable[_T], end: Optional[_T] = None
) -> Iterator[tuple[_T, Optional[_T]]]:
    """Iterate over successive pairs with overhang for last element.

    Parameters
    ----------
    iterable : Iterable[_T]
        Iterable to iterate over.
    end : Optional[_T]
        Value for the overhang (Default value = None)

    Returns
    -------
    Iterator[tuple[_T, Optional[_T]]]
        Iterator yielding the successive pairs.
    """
    left, right = itertools.tee(iterable)
    next(right, None)
    return zip(left, itertools.chain(right, [end]))


KV_REGEX = re.compile(r"^[^\s].*$", flags=re.M)
PARAM_KEY_REGEX = re.compile(r"^(?P<name>.*?)(?:\s+:\s*(?P<type>.*?))?$")
PARAM_OPTIONAL_REGEX = re.compile(r"(?P<type>.*?)(?:, optional|\(optional\))$")

# numpydoc format has no formal grammar for this,
# but we can make some educated guesses...
PARAM_DEFAULT_REGEX = re.compile(
    r"(?<!\S)[Dd]efault(?: is | = |: |s to |)\s*(?P<value>[\w\-\.]*\w)"
)

RETURN_KEY_REGEX = re.compile(r"^(?:(?P<name>.*?)\s*:\s*)?(?P<type>.*?)$")


class Section:
    """Numpydoc section parser."""

    def __init__(self, title: str, key: str) -> None:
        """Initialize a section.

        Parameters
        ----------
        title : str
            section title. For most sections, this is a heading like
            "Parameters" which appears on its own line, underlined by
            en-dashes ('-') on the following line.
        key : str
            meta key string. In the parsed ``DocstringMeta`` instance this
            will be the first element of the ``args`` attribute list.
        """
        self.title = title
        self.key = key

    @property
    def title_pattern(self) -> str:
        """Regular expression pattern matching this section's header.

        This pattern will match this instance's ``title`` attribute in
        an anonymous group.

        Returns
        -------
        str
            Regex pattern as a string.
        """
        dashes = "-" * len(self.title)
        return rf"^({self.title})\s*?\n{dashes}\s*$"

    def parse(self, text: str) -> Iterable[DocstringMeta]:
        """Parse ``DocstringMeta`` objects from the body of this section.

        Parameters
        ----------
        text : str
            section body text. Should be cleaned with
            ``inspect.cleandoc`` before parsing.

        Yields
        ------
        DocstringMeta
            object from this section body.
        """
        yield DocstringMeta([self.key], description=clean_str(text))


class _KVSection(Section):
    """Base parser for numpydoc sections with key-value syntax.

    E.g. sections that look like this:
        key
            value
        key2 : type
            values can also span...
            ... multiple lines
    """

    def _parse_item(self, key: str, value: str) -> DocstringMeta:
        """_summary_.

        Parameters
        ----------
        key : str
            Key of the item to parse
        value : str
            Value of the item to parse

        Raises
        ------
        NotImplementedError
            To be implemented by child classes.
        """
        raise NotImplementedError

    @override
    def parse(self, text: str) -> Iterable[DocstringMeta]:
        """Parse all items in the docstring text.

        Parameters
        ----------
        text : str
            Docstring text to parse.

        Yields
        ------
        DocstringMeta
            Items parsed from the docstring.
        """
        for match, next_match in _pairwise(KV_REGEX.finditer(text)):
            start = match.end()
            end = next_match.start() if next_match is not None else None
            value = text[start:end]
            yield self._parse_item(key=match.group(), value=inspect.cleandoc(value))


class _SphinxSection(Section):
    """Base parser for numpydoc sections with sphinx-style syntax.

    E.g. sections that look like this:
        .. title:: something
            possibly over multiple lines
    """

    @property
    @override
    def title_pattern(self) -> str:
        """Title pattern used by sphinx sections.

        Returns
        -------
        str
            Regex pattern as a string.
        """
        return rf"^\.\.\s*({self.title})\s*::"


class ParamSection(_KVSection):
    """Parser for numpydoc parameter sections.

    E.g. any section that looks like this:
        arg_name
            arg_description
        arg_2 : type, optional
            descriptions can also span...
            ... multiple lines
    """

    @override
    def _parse_item(self, key: str, value: str) -> DocstringParam:
        """Parse item from a parameter section.

        Parameters
        ----------
        key : str
            Key of the item. Contains parameter name and optionally type information.
        value : str
            Description for the item. Also possibly contains default value.

        Returns
        -------
        DocstringParam
            Parsed representation of the parameter item.

        Raises
        ------
        ParseError
            If no key could be parsed.
        ParseError
            If mandatory parts of the section were parsed incorrectly.
        """
        match = PARAM_KEY_REGEX.match(key)
        arg_name = type_name = is_optional = None
        if match is None:
            msg = f"Could not parse param key on line `{key}`"
            raise ParseError(msg)
        arg_name = match.group("name")
        type_name = match.group("type")
        if not isinstance(arg_name, str):
            msg = (
                f"Did not get a string when capturing mandatory section"
                f" 'arg_name' for key line `{key}`. Got `{arg_name}` instead."
            )
            raise ParseError(msg)
        if isinstance(type_name, str):
            optional_match = PARAM_OPTIONAL_REGEX.match(type_name)
            if optional_match is not None:
                type_name = optional_match.group("type")
                is_optional = True
            else:
                is_optional = False
        else:
            type_name = None

        default = None
        if value != "":
            default_match = PARAM_DEFAULT_REGEX.search(value)
            if default_match is not None:
                default = default_match.group("value")

        return DocstringParam(
            args=[self.key, arg_name],
            description=clean_str(value),
            arg_name=arg_name,
            type_name=type_name,
            is_optional=is_optional,
            default=default,
        )


class RaisesSection(_KVSection):
    """Parser for numpydoc raises sections.

    E.g. any section that looks like this:
        ValueError
            A description of what might raise ValueError
    """

    @override
    def _parse_item(self, key: str, value: str) -> DocstringRaises:
        """Parse an item in the raises section.

        Parameters
        ----------
        key : str
            Key of the item to be parsed. Usually name of the exception raised.
        value : str
            Description of the item.

        Returns
        -------
        DocstringRaises
            Parsed representation of the raises item.
        """
        return DocstringRaises(
            args=[self.key, key],
            description=clean_str(value),
            type_name=key if key != "" else None,
        )


class ReturnsSection(_KVSection):
    """Parser for numpydoc returns sections.

    E.g. any section that looks like this:
        return_name : type
            A description of this returned value
        another_type
            Return names are optional, types are required
    """

    is_generator = False

    @override
    def _parse_item(self, key: str, value: str) -> DocstringReturns:
        """Parse an item from the return section.

        Parameters
        ----------
        key : str
            Key of the item (usually type, possibly name + type)
        value : str
            Description of the return value.

        Returns
        -------
        DocstringReturns
            Parsed representation of the return item.
        """
        match = RETURN_KEY_REGEX.match(key)
        if match is not None:
            return_name = match.group("name")
            type_name = match.group("type")
        else:
            return_name = None
            type_name = None

        return DocstringReturns(
            args=[self.key],
            description=clean_str(value),
            type_name=type_name,
            is_generator=self.is_generator,
            return_name=return_name,
        )


class YieldsSection(_KVSection):
    """Parser for numpydoc generator "yields" sections."""

    is_generator = True

    @override
    def _parse_item(self, key: str, value: str) -> DocstringYields:
        """Parse an item from the yield section.

        Parameters
        ----------
        key : str
            Key of the item (usually type, possibly name + type)
        value : str
            Description of the yielded value.

        Returns
        -------
        DocstringYields
            Parsed representation of the yield item.
        """
        match = RETURN_KEY_REGEX.match(key)
        if match is not None:
            yield_name = match.group("name")
            type_name = match.group("type")
        else:
            yield_name = None
            type_name = None

        return DocstringYields(
            args=[self.key],
            description=clean_str(value),
            type_name=type_name,
            is_generator=self.is_generator,
            yield_name=yield_name,
        )


class DeprecationSection(_SphinxSection):
    """Parser for numpydoc "deprecation warning" sections.

    E.g. any section that looks like this:
        .. deprecated:: 1.6.0
            This description has
            multiple lines!
    """

    @override
    def parse(self, text: str) -> Iterable[DocstringDeprecated]:
        """Parse ``DocstringDeprecated`` objects from the body of this section.

        Parameters
        ----------
        text : str
            Text of the deprecation section.

        Yields
        ------
        DocstringDeprecated
            Parsed representation of the deprecation item.

        Raises
        ------
        ParseError
            If the parsed version number was unexpectedly `None`.
            Usually a lack of version number would be represented by an empty string.
        """
        version, desc, *_ = [*text.split(sep="\n", maxsplit=1), None, None]
        if version is None:
            msg = (
                f"Got `None` while parsing version number "
                f"in deprecated section `{text}`."
            )
            raise ParseError(msg)
        if desc is not None:
            desc = clean_str(inspect.cleandoc(desc))

        yield DocstringDeprecated(
            args=[self.key], description=desc, version=clean_str(version)
        )


class ExamplesSection(Section):
    """Parser for numpydoc examples sections.

    E.g. any section that looks like this:

        Optional description for the following example. Always preceded
        and followed by an empty line. Except for the first description.

        >>> import numpy.matlib
        >>> np.matlib.empty((2, 2))    # filled with random data
        matrix([[  6.76425276e-320,   9.79033856e-307], # random
                [  7.39337286e-309,   3.22135945e-309]])

        Description for the second example.

        >>> d = np.zeros((5,2))
        >>> for i in range(5):
        ...   for j in range(2):
        ...     for k in range(3):
        ...       for n in range(4):
        ...         d[i,j] += a[k,n,i] * b[n,k,j]
        >>> c == d
        array([[ True,  True],
            [ True,  True],
            [ True,  True],
            [ True,  True],
            [ True,  True]])
    """

    @override
    def parse(self, text: str) -> Iterable[DocstringExample]:
        """Parse ``DocstringExample`` objects from the body of this section.

        Parameters
        ----------
        text : str
            section body text. Should be cleaned with
            ``inspect.cleandoc`` before parsing.

        Yields
        ------
        DocstringExample
            Docstring example sections
        """
        # Reverse so that we can efficiently pop from the back
        # instead of doing constant pops from the front.
        # Could also use a deque
        # ---
        # We add a newline to the end to not have to special case the first
        # description.
        lines = [*list(reversed(dedent(text).strip().splitlines())), "\n"]
        while lines:
            snippet_lines: list[str] = []
            description_lines: list[str] = []
            # Empty lines before the description
            while lines and lines[-1].strip() == "":
                lines.pop()
            # Description. Should not start with ">>>". if that were the case
            # Then there was no description.
            while lines and lines[-1].strip() != "" and not lines[-1].startswith(">>>"):
                description_lines.append(lines.pop())
            # Empty lines after description
            while lines and lines[-1].strip() == "":
                lines.pop()
            # Here the actual example starts.
            # We take any line.
            # The code part starts with ">>>" or "..."
            # but the result part can be anything.
            # Just keeping until an empty line which should indicate the next example.
            while lines and lines[-1].strip() != "":
                snippet_lines.append(lines.pop())
            yield DocstringExample(
                [self.key],
                snippet="\n".join(snippet_lines) if snippet_lines else None,
                description="\n".join(description_lines),
            )


DEFAULT_SECTIONS = [
    ParamSection("Parameters", "param"),
    ParamSection("Params", "param"),
    ParamSection("Arguments", "param"),
    ParamSection("Args", "param"),
    ParamSection("Other Parameters", "other_param"),
    ParamSection("Other Params", "other_param"),
    ParamSection("Other Arguments", "other_param"),
    ParamSection("Other Args", "other_param"),
    ParamSection("Receives", "receives"),
    ParamSection("Receive", "receives"),
    RaisesSection("Raises", "raises"),
    RaisesSection("Raise", "raises"),
    RaisesSection("Warns", "warns"),
    RaisesSection("Warn", "warns"),
    ParamSection("Attributes", "attribute"),
    ParamSection("Attribute", "attribute"),
    ParamSection("Methods", "method"),
    ParamSection("Method", "method"),
    ReturnsSection("Returns", "returns"),
    ReturnsSection("Return", "returns"),
    YieldsSection("Yields", "yields"),
    YieldsSection("Yield", "yields"),
    ExamplesSection("Examples", "examples"),
    ExamplesSection("Example", "examples"),
    Section("Warnings", "warnings"),
    Section("Warning", "warnings"),
    Section("See Also", "see_also"),
    Section("Related", "see_also"),
    Section("Notes", "notes"),
    Section("Note", "notes"),
    Section("References", "references"),
    Section("Reference", "references"),
    DeprecationSection("deprecated", "deprecation"),
]


class NumpydocParser:
    """Parser for numpydoc-style docstrings."""

    def __init__(self, sections: Optional[Iterable[Section]] = None) -> None:
        """Set up sections.

        Parameters
        ----------
        sections : Optional[Iterable[Section]]
            Recognized sections or None to defaults.
        """
        self.sections = {s.title: s for s in (sections or DEFAULT_SECTIONS)}
        self._setup()

    def _setup(self) -> None:
        """Set up parser title regex."""
        self.titles_re = re.compile(
            r"|".join(s.title_pattern for s in self.sections.values()),
            flags=re.M,
        )

    def add_section(self, section: Section) -> None:
        """Add or replace a section.

        Parameters
        ----------
        section : Section
            The new section.
        """
        self.sections[section.title] = section
        self._setup()

    def parse(self, text: Optional[str]) -> Docstring:
        """Parse the numpy-style docstring into its components.

        Parameters
        ----------
        text : Optional[str]
            docstring text

        Returns
        -------
        Docstring
            parsed docstring
        """
        ret = Docstring(style=DocstringStyle.NUMPYDOC)
        if not text:
            return ret

        # Clean according to PEP-0257
        text = inspect.cleandoc(text)

        if match := self.titles_re.search(text):
            desc_chunk = text[: match.start()]
            meta_chunk = text[match.start() :]
        else:
            desc_chunk = text
            meta_chunk = ""

        # Break description into short and long parts
        split_description(ret, desc_chunk)

        for match, nextmatch in _pairwise(self.titles_re.finditer(meta_chunk)):
            title = next(g for g in match.groups() if g is not None)
            factory = self.sections[title]

            # section chunk starts after the header,
            # ends at the start of the next header
            start = match.end()
            end = nextmatch.start() if nextmatch is not None else None
            ret.meta.extend(factory.parse(meta_chunk[start:end]))

        return ret


def parse(text: Optional[str]) -> Docstring:
    """Parse the numpy-style docstring into its components.

    Parameters
    ----------
    text : Optional[str]
        docstring text

    Returns
    -------
    Docstring
        parsed docstring
    """
    return NumpydocParser().parse(text)


def process_examples(examples: list[DocstringExample], parts: list[str]) -> None:
    """Add string representation of examples section to parts.

    Parameters
    ----------
    examples : list[DocstringExample]
        DocstringExamples to add to parts.
    parts : list[str]
        List of strings representing the final output of compose().
    indent : str
        the characters used as indentation in the docstring string
        (Default value = '    ')
    """
    if examples:
        parts.append("")
        parts.append("Examples")
        parts.append("-" * len(parts[-1]))
        for i, example in enumerate(examples):
            # Leave out newline for first example
            if i != 0:
                parts.append("\n")
            if example.description:
                parts.append("\n".join(example.description.splitlines()))
                # Only add a new line if we have an actual example snippet here.
                # If not the next description will handle it.
                if example.snippet:
                    parts.append("\n")
            if example.snippet:
                parts.append("\n".join(example.snippet.splitlines()))


def compose(  # noqa: PLR0915
    # pylint: disable=W0613,R0915
    docstring: Docstring,
    rendering_style: RenderingStyle = RenderingStyle.COMPACT,  # noqa: ARG001
    indent: str = "    ",
) -> str:
    """Render a parsed docstring into docstring text.

    Parameters
    ----------
    docstring : Docstring
        parsed docstring representation
    rendering_style : RenderingStyle
        the style to render docstrings (Default value = RenderingStyle.COMPACT)
    indent : str
        the characters used as indentation in the docstring string
        (Default value = '    ')

    Returns
    -------
    str
        docstring text
    """

    def process_one(one: MainSections) -> None:
        """Build the output text for one entry in a section.

        Parameters
        ----------
        one : MainSections
            Docstring for which to build the raw text.
        """
        if isinstance(one, DocstringParam):
            head = one.arg_name
        elif isinstance(one, DocstringReturns):
            head = one.return_name
        elif isinstance(one, DocstringYields):
            head = one.yield_name
        else:
            head = None

        if one.type_name and head:
            head += f" : {one.type_name}"
        elif one.type_name:
            head = one.type_name
        elif not head:
            head = ""

        if isinstance(one, DocstringParam) and one.is_optional:
            head += ", optional"

        if one.description:
            body = f"\n{indent}".join([head, *one.description.splitlines()])
            parts.append(body)
        else:
            parts.append(head)

    def process_sect(name: str, args: list[MainSections]) -> None:
        """Build the output for a docstring section.

        Parameters
        ----------
        name : str
            Section for which to build the output.
        args : list[MainSections]
            List of individual elements of that section.
        """
        if args:
            parts.append("")
            parts.append(name)
            parts.append("-" * len(name))
            for arg in args:
                process_one(arg)

    parts: list[str] = []
    if docstring.short_description:
        parts.append(docstring.short_description)
    if docstring.blank_after_short_description:
        parts.append("")

    if docstring.deprecation:
        first = ".. deprecated::"
        if docstring.deprecation.version:
            first += f" {docstring.deprecation.version}"
        if docstring.deprecation.description:
            rest = docstring.deprecation.description.splitlines()
        else:
            rest = []
        sep = f"\n{indent}"
        parts.append(sep.join([first, *rest]))

    if docstring.long_description:
        parts.append(docstring.long_description)
    if docstring.blank_after_long_description:
        parts.append("")

    process_sect(
        "Parameters",
        [item for item in docstring.params or [] if item.args[0] == "param"],
    )

    process_sect(
        "Attributes",
        [item for item in docstring.params or [] if item.args[0] == "attribute"],
    )

    process_sect(
        "Methods",
        [item for item in docstring.params or [] if item.args[0] == "method"],
    )

    process_sect(
        "Returns",
        list(docstring.many_returns or []),
    )

    process_sect(
        "Yields",
        list(docstring.many_yields or []),
    )

    if docstring.returns and not docstring.many_returns:
        ret = docstring.returns
        parts.append("Yields" if ret else "Returns")
        parts.append("-" * len(parts[-1]))
        process_one(ret)

    process_sect(
        "Receives",
        [item for item in docstring.params or [] if item.args[0] == "receives"],
    )

    process_sect(
        "Other Parameters",
        [item for item in docstring.params or [] if item.args[0] == "other_param"],
    )

    process_sect(
        "Raises",
        [item for item in docstring.raises or [] if item.args[0] == "raises"],
    )

    process_sect(
        "Warns",
        [item for item in docstring.raises or [] if item.args[0] == "warns"],
    )

    process_examples(docstring.examples, parts)

    for meta in docstring.meta:
        if isinstance(
            meta,
            (
                DocstringDeprecated,
                DocstringParam,
                DocstringReturns,
                DocstringRaises,
                DocstringYields,
                DocstringExample,
            ),
        ):
            continue  # Already handled

        parts.append("")
        parts.append(meta.args[0].replace("_", "").title())
        parts.append("-" * len(meta.args[0]))

        if meta.description:
            parts.append(meta.description)

    return "\n".join(parts)
