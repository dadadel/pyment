"""ReST-style docstring parsing."""

import inspect
import re
from typing import Optional

from .common import (
    DEPRECATION_KEYWORDS,
    PARAM_KEYWORDS,
    RAISES_KEYWORDS,
    RETURNS_KEYWORDS,
    YIELDS_KEYWORDS,
    Docstring,
    DocstringDeprecated,
    DocstringMeta,
    DocstringParam,
    DocstringRaises,
    DocstringReturns,
    DocstringStyle,
    DocstringYields,
    ParseError,
    RenderingStyle,
)


def _build_meta(args: list[str], desc: str) -> DocstringMeta:  # noqa: PLR0912
    key = args[0]

    if key in PARAM_KEYWORDS:
        if len(args) == 3:
            key, type_name, arg_name = args
            if type_name.endswith("?"):
                is_optional = True
                type_name = type_name[:-1]
            else:
                is_optional = False
        elif len(args) == 2:
            key, arg_name = args
            type_name = None
            is_optional = None
        else:
            msg = f"Expected one or two arguments for a {key} keyword."
            raise ParseError(msg)

        match = re.match(r".*defaults to (.+)", desc, flags=re.DOTALL)
        default = match[1].rstrip(".") if match else None

        return DocstringParam(
            args=args,
            description=desc,
            arg_name=arg_name,
            type_name=type_name,
            is_optional=is_optional,
            default=default,
        )

    if key in RETURNS_KEYWORDS:
        if len(args) == 2:
            type_name = args[1]
        elif len(args) == 1:
            type_name = None
        else:
            msg = f"Expected one or no arguments for a {key} keyword."
            raise ParseError(msg)

        return DocstringReturns(
            args=args,
            description=desc,
            type_name=type_name,
            is_generator=False,
        )

    if key in YIELDS_KEYWORDS:
        if len(args) == 2:
            type_name = args[1]
        elif len(args) == 1:
            type_name = None
        else:
            msg = f"Expected one or no arguments for a {key} keyword."
            raise ParseError(msg)

        return DocstringYields(
            args=args,
            description=desc,
            type_name=type_name,
            is_generator=True,
        )

    if key in DEPRECATION_KEYWORDS:
        match = re.search(
            r"^(?P<version>v?((?:\d+)(?:\.[0-9a-z\.]+))) (?P<desc>.+)",
            desc,
            flags=re.I,
        )
        return DocstringDeprecated(
            args=args,
            version=match["version"] if match else None,
            description=match["desc"] if match else desc,
        )

    if key in RAISES_KEYWORDS:
        if len(args) == 2:
            type_name = args[1]
        elif len(args) == 1:
            type_name = None
        else:
            msg = f"Expected one or no arguments for a {key} keyword."
            raise ParseError(msg)
        return DocstringRaises(args=args, description=desc, type_name=type_name)

    return DocstringMeta(args=args, description=desc)


def parse(text: Optional[str]) -> Docstring:  # noqa: PLR0912
    """Parse the ReST-style docstring into its components.

    Parameters
    ----------
    text : str
        docstring to parse

    Returns
    -------
    Docstring
        parsed docstring

    Raises
    ------
    ParseError
        If a section does not have two colons to be split on.
    """
    ret = Docstring(style=DocstringStyle.REST)
    if not text:
        return ret

    text = inspect.cleandoc(text)
    if match := re.search("^:", text, flags=re.M):
        desc_chunk = text[: match.start()]
        meta_chunk = text[match.start() :]
    else:
        desc_chunk = text
        meta_chunk = ""

    parts = desc_chunk.split("\n", 1)
    ret.short_description = parts[0] or None
    if len(parts) > 1:
        long_desc_chunk = parts[1] or ""
        ret.blank_after_short_description = long_desc_chunk.startswith("\n")
        ret.blank_after_long_description = long_desc_chunk.endswith("\n\n")
        ret.long_description = long_desc_chunk.strip() or None

    types = {}
    rtypes = {}
    ytypes = {}
    for match in re.finditer(r"(^:.*?)(?=^:|\Z)", meta_chunk, flags=re.S | re.M):
        chunk = match.group(0)
        if not chunk:
            continue
        try:
            args_chunk, desc_chunk = chunk.lstrip(":").split(":", 1)
        except ValueError as ex:
            msg = f'Error parsing meta information near "{chunk}".'
            raise ParseError(msg) from ex
        args = args_chunk.split()
        desc = desc_chunk.strip()

        if "\n" in desc:
            first_line, rest = desc.split("\n", 1)
            desc = first_line + "\n" + inspect.cleandoc(rest)

        # Add special handling for :type a: typename
        if len(args) == 2 and args[0] == "type":
            types[args[1]] = desc
        elif len(args) in {1, 2} and args[0] == "rtype":
            rtypes[None if len(args) == 1 else args[1]] = desc
        elif len(args) in {1, 2} and args[0] == "ytype":
            ytypes[None if len(args) == 1 else args[1]] = desc
        else:
            ret.meta.append(_build_meta(args, desc))

    for meta in ret.meta:
        if isinstance(meta, DocstringParam):
            meta.type_name = meta.type_name or types.get(meta.arg_name)
        elif isinstance(meta, DocstringReturns):
            meta.type_name = meta.type_name or rtypes.get(meta.return_name)
        elif isinstance(meta, DocstringYields):
            meta.type_name = meta.type_name or ytypes.get(meta.yield_name)

    if not any(isinstance(m, DocstringReturns) for m in ret.meta) and rtypes:
        for return_name, type_name in rtypes.items():
            ret.meta.append(
                DocstringReturns(
                    args=[],
                    type_name=type_name,
                    description=None,
                    is_generator=False,
                    return_name=return_name,
                )
            )

    return ret


def compose(  # noqa: PLR0915, PLR0912
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
        the characters used as indentation in the docstring string
        (Default value = '    ')

    Returns
    -------
    str
        docstring text
    """

    def process_desc(desc: Optional[str]) -> str:
        if not desc:
            return ""

        if rendering_style == RenderingStyle.CLEAN:
            (first, *rest) = desc.splitlines()
            return "\n".join([f" {first}"] + [indent + line for line in rest])

        if rendering_style == RenderingStyle.EXPANDED:
            (first, *rest) = desc.splitlines()
            return "\n".join(["\n" + indent + first] + [indent + line for line in rest])

        return f" {desc}"

    parts: list[str] = []
    if docstring.short_description:
        parts.append(docstring.short_description)
    if docstring.blank_after_short_description:
        parts.append("")
    if docstring.long_description:
        parts.append(docstring.long_description)
    if docstring.blank_after_long_description:
        parts.append("")

    for meta in docstring.meta:
        if isinstance(meta, DocstringParam):
            if meta.type_name:
                type_text = (
                    f" {meta.type_name}? "
                    if meta.is_optional
                    else f" {meta.type_name} "
                )
            else:
                type_text = " "
            if rendering_style == RenderingStyle.EXPANDED:
                text = f":param {meta.arg_name}:"
                text += process_desc(meta.description)
                parts.append(text)
                if type_text[:-1]:
                    parts.append(f":type {meta.arg_name}:{type_text[:-1]}")
            else:
                text = f":param{type_text}{meta.arg_name}:"
                text += process_desc(meta.description)
                parts.append(text)
        elif isinstance(meta, (DocstringReturns, DocstringYields)):
            type_text = f" {meta.type_name}" if meta.type_name else ""
            key = "yields" if isinstance(meta, DocstringYields) else "returns"

            if rendering_style == RenderingStyle.EXPANDED:
                if meta.description:
                    text = f":{key}:"
                    text += process_desc(meta.description)
                    parts.append(text)
                if type_text:
                    return_key = (
                        "rtype" if isinstance(meta, DocstringReturns) else "ytype"
                    )
                    parts.append(f":{return_key}:{type_text}")
            else:
                text = f":{key}{type_text}:"
                text += process_desc(meta.description)
                parts.append(text)
        elif isinstance(meta, DocstringRaises):
            type_text = f" {meta.type_name} " if meta.type_name else ""
            text = f":raises{type_text}:{process_desc(meta.description)}"
            parts.append(text)
        else:
            text = f':{" ".join(meta.args)}:{process_desc(meta.description)}'
            parts.append(text)
    return "\n".join(parts)
