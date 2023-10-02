"""Google-style docstring parsing."""

import inspect
import re
from collections import OrderedDict
from enum import IntEnum
from typing import Any, List, Mapping, NamedTuple, Optional, Union

from .common import (
    EXAMPLES_KEYWORDS,
    PARAM_KEYWORDS,
    RAISES_KEYWORDS,
    RETURNS_KEYWORDS,
    YIELDS_KEYWORDS,
    Docstring,
    DocstringExample,
    DocstringMeta,
    DocstringParam,
    DocstringRaises,
    DocstringReturns,
    DocstringStyle,
    DocstringYields,
    ParseError,
    RenderingStyle,
)


class SectionType(IntEnum):
    """Types of sections."""

    SINGULAR = 0
    """For sections like examples."""

    MULTIPLE = 1
    """For sections like params."""

    SINGULAR_OR_MULTIPLE = 2
    """For sections like returns or yields."""


class Section(NamedTuple):
    """A docstring section."""

    title: str
    key: str
    type_info: SectionType


GOOGLE_TYPED_ARG_REGEX = re.compile(r"\s*(.+?)\s*\(\s*(.*[^\s]+)\s*\)")
GOOGLE_ARG_DESC_REGEX = re.compile(r".*\. Defaults to (.+)\.")
MULTIPLE_PATTERN = re.compile(
    r"(\s*[^:\s]+:)|([^:]*\]:.*)|(\s*[^|\s]+(\s*\|\s*[^|\s]+)*:)"
)

DEFAULT_SECTIONS = [
    Section("Arguments", "param", SectionType.MULTIPLE),
    Section("Args", "param", SectionType.MULTIPLE),
    Section("Parameters", "param", SectionType.MULTIPLE),
    Section("Params", "param", SectionType.MULTIPLE),
    Section("Raises", "raises", SectionType.MULTIPLE),
    Section("Exceptions", "raises", SectionType.MULTIPLE),
    Section("Except", "raises", SectionType.MULTIPLE),
    Section("Attributes", "attribute", SectionType.MULTIPLE),
    Section("Example", "examples", SectionType.SINGULAR),
    Section("Examples", "examples", SectionType.SINGULAR),
    Section("Returns", "returns", SectionType.SINGULAR_OR_MULTIPLE),
    Section("Yields", "yields", SectionType.SINGULAR_OR_MULTIPLE),
]


class GoogleParser:
    """Parser for Google-style docstrings."""

    def __init__(
        self, sections: Optional[List[Section]] = None, *, title_colon: bool = True
    ) -> None:
        """Set up sections.

        Parameters
        ----------
        sections : Optional[List[Section]]
            Recognized sections or None to defaults.
        title_colon : _type_
            require colon after section title. (Default value = True)
        """
        if not sections:
            sections = DEFAULT_SECTIONS
        self.sections = {s.title: s for s in sections}
        self.title_colon = title_colon
        self._setup()

    def _setup(self) -> None:
        colon = ":" if self.title_colon else ""
        self.titles_re = re.compile(
            "^("
            + "|".join(f"({t})" for t in self.sections)
            + ")"
            + colon
            + "[ \t\r\f\v]*$",
            flags=re.M,
        )

    def _build_meta(self, text: str, title: str) -> DocstringMeta:
        """Build docstring element.

        Parameters
        ----------
        text : str
            docstring element text
        title : str
            title of section containing element

        Returns
        -------
        DocstringMeta
            docstring meta element

        Raises
        ------
        ParseError
            If the text lacks a colon ':'
        """
        section = self.sections[title]

        if (
            section.type_info == SectionType.SINGULAR_OR_MULTIPLE
            and not MULTIPLE_PATTERN.match(text)
        ) or section.type_info == SectionType.SINGULAR:
            return self._build_single_meta(section, text)

        if ":" not in text:
            msg = f"Expected a colon in {text!r}."
            raise ParseError(msg)

        # Split spec and description
        before, desc = text.split(":", 1)
        if desc:
            desc = desc[1:] if desc[0] == " " else desc
            if "\n" in desc:
                first_line, rest = desc.split("\n", 1)
                desc = first_line + "\n" + inspect.cleandoc(rest)
            desc = desc.strip("\n")

        return self._build_multi_meta(section, before, desc)

    @staticmethod
    def _build_single_meta(section: Section, desc: str) -> DocstringMeta:
        if section.key in RETURNS_KEYWORDS:
            return DocstringReturns(
                args=[section.key],
                description=desc,
                type_name=None,
                is_generator=False,
            )
        if section.key in YIELDS_KEYWORDS:
            return DocstringYields(
                args=[section.key],
                description=desc,
                type_name=None,
                is_generator=True,
            )
        if section.key in RAISES_KEYWORDS:
            return DocstringRaises(args=[section.key], description=desc, type_name=None)
        if section.key in EXAMPLES_KEYWORDS:
            return DocstringExample(args=[section.key], snippet=None, description=desc)
        if section.key in PARAM_KEYWORDS:
            msg = "Expected paramenter name."
            raise ParseError(msg)
        return DocstringMeta(args=[section.key], description=desc)

    @staticmethod
    def _build_multi_meta(section: Section, before: str, desc: str) -> DocstringMeta:
        if section.key in PARAM_KEYWORDS:
            match = GOOGLE_TYPED_ARG_REGEX.match(before)
            if match:
                arg_name, type_name = match.group(1, 2)
                if type_name.endswith(", optional"):
                    is_optional = True
                    type_name = type_name[:-10]
                elif type_name.endswith("?"):
                    is_optional = True
                    type_name = type_name[:-1]
                else:
                    is_optional = False
            else:
                arg_name, type_name = before, None
                is_optional = None

            match = GOOGLE_ARG_DESC_REGEX.match(desc)
            default = match.group(1) if match else None

            return DocstringParam(
                args=[section.key, before],
                description=desc,
                arg_name=arg_name,
                type_name=type_name,
                is_optional=is_optional,
                default=default,
            )
        if section.key in RETURNS_KEYWORDS:
            return DocstringReturns(
                args=[section.key, before],
                description=desc,
                type_name=before,
                is_generator=False,
            )
        if section.key in YIELDS_KEYWORDS:
            return DocstringYields(
                args=[section.key, before],
                description=desc,
                type_name=before,
                is_generator=True,
            )
        if section.key in RAISES_KEYWORDS:
            return DocstringRaises(
                args=[section.key, before], description=desc, type_name=before
            )
        return DocstringMeta(args=[section.key, before], description=desc)

    def add_section(self, section: Section) -> None:
        """Add or replace a section.

        :param section: The new section.
        """
        self.sections[section.title] = section
        self._setup()

    def parse(self, text: str) -> Docstring:  # noqa: PLR0912
        """Parse the Google-style docstring into its components.

        Parameters
        ----------
        text : str
            docstring text

        Returns
        -------
        Docstring
            parsed docstring
        """
        ret = Docstring(style=DocstringStyle.GOOGLE)
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
        parts = desc_chunk.split("\n", 1)
        ret.short_description = parts[0] or None
        if len(parts) > 1:
            long_desc_chunk = parts[1] or ""
            ret.blank_after_short_description = long_desc_chunk.startswith("\n")
            ret.blank_after_long_description = long_desc_chunk.endswith("\n\n")
            ret.long_description = long_desc_chunk.strip() or None

        # Split by sections determined by titles
        matches = list(self.titles_re.finditer(meta_chunk))
        if not matches:
            return ret
        splits = [
            (matches[j].end(), matches[j + 1].start()) for j in range(len(matches) - 1)
        ]
        splits.append((matches[-1].end(), len(meta_chunk)))

        chunks: Mapping[str, str] = OrderedDict()
        for j, (start, end) in enumerate(splits):
            title = matches[j].group(1)
            if title not in self.sections:
                continue

            # Clear Any Unknown Meta
            # Ref: https://github.com/rr-/docstring_parser/issues/29
            meta_details = meta_chunk[start:end]
            unknown_meta = re.search(r"\n\S", meta_details)
            if unknown_meta is not None:
                meta_details = meta_details[: unknown_meta.start()]

            chunks[title] = meta_details.strip("\n")
        if not chunks:
            return ret

        # Add elements from each chunk
        for title, chunk in chunks.items():
            # Determine indent
            indent_match = re.search(r"^\s*", chunk)
            if not indent_match:
                msg = f'Can\'t infer indent from "{chunk}"'
                raise ParseError(msg)
            indent = indent_match.group()

            # Check for singular elements
            if self.sections[title].type_info in [
                SectionType.SINGULAR,
                SectionType.SINGULAR_OR_MULTIPLE,
            ]:
                part = inspect.cleandoc(chunk)
                ret.meta.append(self._build_meta(part, title))
                continue

            # Split based on lines which have exactly that indent
            _re = rf"^{indent}(?=\S)"
            c_matches = list(re.finditer(_re, chunk, flags=re.M))
            if not c_matches:
                msg = f'No specification for "{title}": "{chunk}"'
                raise ParseError(msg)
            c_splits = [
                (c_cur.end(), c_next.start())
                for c_cur, c_next in zip(c_matches, c_matches[1:], strict=False)
            ]
            c_splits.append((c_matches[-1].end(), len(chunk)))
            for start, end in c_splits:
                part = chunk[start:end].strip("\n")
                ret.meta.append(self._build_meta(part, title))

        return ret


def parse(text: str) -> Docstring:
    """Parse the Google-style docstring into its components.

    :returns: parsed docstring
    """
    return GoogleParser().parse(text)


def compose(  # noqa: PLR0915
    docstring: Docstring,
    rendering_style: RenderingStyle = RenderingStyle.COMPACT,
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
        the characters used as indentation in the
        docstring string (Default value = '    ')

    Returns
    -------
    str
        docstring text
    """

    def process_one(
        one: Union[DocstringParam, DocstringReturns, DocstringRaises, DocstringYields]
    ) -> None:
        head = ""

        if isinstance(one, DocstringParam):
            head += one.arg_name or ""
        elif isinstance(one, DocstringReturns):
            head += one.return_name or ""
        elif isinstance(one, DocstringYields):
            head += one.yield_name or ""

        if isinstance(one, DocstringParam) and one.is_optional:
            optional = (
                "?" if rendering_style == RenderingStyle.COMPACT else ", optional"
            )
        else:
            optional = ""

        if one.type_name and head:
            head += f" ({one.type_name}{optional}):"
        elif one.type_name:
            head += f"{one.type_name}{optional}:"
        else:
            head += ":"
        head = indent + head

        if one.description and rendering_style == RenderingStyle.EXPANDED:
            body = f"\n{indent}{indent}".join([head, *one.description.splitlines()])
            parts.append(body)
        elif one.description:
            (first, *rest) = one.description.splitlines()
            body = f"\n{indent}{indent}".join([f"{head} {first}", *rest])
            parts.append(body)
        else:
            parts.append(head)

    def process_sect(name: str, args: List[Any]) -> None:
        if args:
            parts.append(name)
            for arg in args:
                process_one(arg)
            parts.append("")

    parts: List[str] = []
    if docstring.short_description:
        parts.append(docstring.short_description)
    if docstring.blank_after_short_description:
        parts.append("")

    if docstring.long_description:
        parts.append(docstring.long_description)
    if docstring.blank_after_long_description:
        parts.append("")

    process_sect("Args:", [p for p in docstring.params or [] if p.args[0] == "param"])

    process_sect(
        "Attributes:",
        [p for p in docstring.params or [] if p.args[0] == "attribute"],
    )

    process_sect(
        "Returns:",
        docstring.many_returns,
    )

    process_sect("Yields:", docstring.many_yields)

    process_sect("Raises:", docstring.raises or [])

    if docstring.returns and not docstring.many_returns:
        ret = docstring.returns
        parts.append("Yields:" if ret else "Returns:")
        parts.append("-" * len(parts[-1]))
        process_one(ret)

    for meta in docstring.meta:
        if isinstance(
            meta, (DocstringParam, DocstringReturns, DocstringRaises, DocstringYields)
        ):
            continue  # Already handled
        parts.append(meta.args[0].replace("_", "").title() + ":")
        if meta.description:
            lines = [indent + line for line in meta.description.splitlines()]
            parts.append("\n".join(lines))
        parts.append("")

    while parts and not parts[-1]:
        parts.pop()

    return "\n".join(parts)
