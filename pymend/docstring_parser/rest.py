"""ReST-style docstring parsing."""

import inspect
import re
from typing import Optional, Union

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
    append_description,
    split_description,
)


def _build_param(args: list[str], desc: str) -> DocstringParam:
    """Build parameter entry from supplied arguments.

    Parameters
    ----------
    args : list[str]
        List of strings describing the parameter (name, type)
    desc : str
        String representing the parameter description.

    Returns
    -------
    DocstringParam
        The docstring object combining and structuring the raw info.

    Raises
    ------
    ParseError
        If an unexpected number of arguments were found.
    """
    if len(args) == 3:
        _, type_name, arg_name = args
        if type_name.endswith("?"):
            is_optional = True
            type_name = type_name[:-1]
        else:
            is_optional = False
    elif len(args) == 2:
        _, arg_name = args
        type_name = None
        is_optional = None
    else:
        msg = f"Expected one or two arguments for a {args[0]} keyword."
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


def _build_return(args: list[str], desc: str) -> DocstringReturns:
    """Build return entry from supplied arguments.

    Parameters
    ----------
    args : list[str]
        List of strings describing the return value (name, type)
    desc : str
        String representing the return description.

    Returns
    -------
    DocstringReturns
        The docstring object combining and structuring the raw info.

    Raises
    ------
    ParseError
        If an unexpected number of arguments were found.
    """
    if len(args) == 2:
        type_name = args[1]
    elif len(args) == 1:
        type_name = None
    else:
        msg = f"Expected one or no arguments for a {args[0]} keyword."
        raise ParseError(msg)

    return DocstringReturns(
        args=args,
        description=desc,
        type_name=type_name,
        is_generator=False,
    )


def _build_yield(args: list[str], desc: str) -> DocstringYields:
    """Build yield entry from supplied arguments.

    Parameters
    ----------
    args : list[str]
        List of strings describing the yielded value (name, type)
    desc : str
        String representing the yield value description.

    Returns
    -------
    DocstringYields
        The docstring object combining and structuring the raw info.

    Raises
    ------
    ParseError
        If an unexpected number of arguments were found.
    """
    if len(args) == 2:
        type_name = args[1]
    elif len(args) == 1:
        type_name = None
    else:
        msg = f"Expected one or no arguments for a {args[0]} keyword."
        raise ParseError(msg)

    return DocstringYields(
        args=args,
        description=desc,
        type_name=type_name,
        is_generator=True,
    )


def _build_deprecation(args: list[str], desc: str) -> DocstringDeprecated:
    """Build deprecation entry from supplied arguments.

    Parameters
    ----------
    args : list[str]
        List of strings describing the deprecation
    desc : str
        Actual textual description.

    Returns
    -------
    DocstringDeprecated
        The docstring object combining and structuring the raw info.
    """
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


def _build_raises(args: list[str], desc: str) -> DocstringRaises:
    """Build raises entry from supplied arguments.

    Parameters
    ----------
    args : list[str]
        List of strings describing the raised value (name, type)
    desc : str
        String representing the raised value description.

    Returns
    -------
    DocstringRaises
        The docstring object combining and structuring the raw info.

    Raises
    ------
    ParseError
        If an unexpected number of arguments were found.
    """
    if len(args) == 2:
        type_name = args[1]
    elif len(args) == 1:
        type_name = None
    else:
        msg = f"Expected one or no arguments for a {args[0]} keyword."
        raise ParseError(msg)
    return DocstringRaises(args=args, description=desc, type_name=type_name)


def _build_meta(args: list[str], desc: str) -> DocstringMeta:
    """Build a fottomg meta entry from supplied arguments.

    Parameters
    ----------
    args : list[str]
        List of strings describing entry.
    desc : str
        String representing the entry description.

    Returns
    -------
    DocstringMeta
        The docstring object combining and structuring the raw info.
    """
    key = args[0]

    if key in PARAM_KEYWORDS:
        return _build_param(args, desc)

    if key in RETURNS_KEYWORDS:
        return _build_return(args, desc)

    if key in YIELDS_KEYWORDS:
        return _build_yield(args, desc)

    if key in DEPRECATION_KEYWORDS:
        return _build_deprecation(args, desc)

    if key in RAISES_KEYWORDS:
        return _build_raises(args, desc)

    return DocstringMeta(args=args, description=desc)


def _get_chunks(text: str) -> tuple[str, str]:
    """Split the text into args (key, type, ...) and description.

    Parameters
    ----------
    text : str
        Text to split into chunks.

    Returns
    -------
    tuple[str, str]
        Args and description.
    """
    if match := re.search("^:", text, flags=re.M):
        return text[: match.start()], text[match.start() :]
    return text, ""


def _get_split_chunks(chunk: str) -> tuple[list[str], str]:
    """Split a entry into args and description.

    Parameters
    ----------
    chunk : str
        Entry string to split.

    Returns
    -------
    tuple[list[str], str]
        Arguments of the entry and its description.

    Raises
    ------
    ParseError
        If the chunk could not be split into args and description.
    """
    try:
        args_chunk, desc_chunk = chunk.lstrip(":").split(":", 1)
    except ValueError as ex:
        msg = f'Error parsing meta information near "{chunk}".'
        raise ParseError(msg) from ex
    return args_chunk.split(), desc_chunk.strip()


def _extract_type_info(
    docstring: Docstring, meta_chunk: str
) -> tuple[dict[str, str], dict[Optional[str], str], dict[Optional[str], str]]:
    """Extract type and description pairs and add other entries directly.

    Parameters
    ----------
    docstring : Docstring
        Docstring wrapper to add information to.
    meta_chunk : str
        Docstring text to extract information from.

    Returns
    -------
    types : dict[str, str]
        Dictionary matching parameters to their descriptions
    rtypes : dict[Optional[str], str]
        Dictionary matching return values to their descriptions
    ytypes : dict[Optional[str], str]
        Dictionary matching yielded values to their descriptions
    """
    types: dict[str, str] = {}
    rtypes: dict[Optional[str], str] = {}
    ytypes: dict[Optional[str], str] = {}
    for chunk_match in re.finditer(r"(^:.*?)(?=^:|\Z)", meta_chunk, flags=re.S | re.M):
        chunk = chunk_match.group(0)
        if not chunk:
            continue

        args, desc = _get_split_chunks(chunk)

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
            docstring.meta.append(_build_meta(args, desc))
    return types, rtypes, ytypes


def parse(text: Optional[str]) -> Docstring:
    """Parse the ReST-style docstring into its components.

    Parameters
    ----------
    text : Optional[str]
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
    desc_chunk, meta_chunk = _get_chunks(text)

    split_description(ret, desc_chunk)

    types, rtypes, ytypes = _extract_type_info(ret, meta_chunk)

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


def process_desc(
    desc: Optional[str], rendering_style: RenderingStyle, indent: str = "    "
) -> str:
    """Process the description for one element.

    Parameters
    ----------
    desc : Optional[str]
        Description to process
    rendering_style : RenderingStyle
        Rendering style to use.
    indent : str
        Indentation needed for that line (Default value = '    ')

    Returns
    -------
    str
        String representation of the docstrings description.
    """
    if not desc:
        return ""

    if rendering_style == RenderingStyle.CLEAN:
        (first, *rest) = desc.splitlines()
        return "\n".join([f" {first}"] + [indent + line for line in rest])

    if rendering_style == RenderingStyle.EXPANDED:
        (first, *rest) = desc.splitlines()
        return "\n".join(["\n" + indent + first] + [indent + line for line in rest])

    return f" {desc}"


def _append_param(
    param: DocstringParam,
    parts: list[str],
    rendering_style: RenderingStyle,
    indent: str,
) -> None:
    """Append one parameter entry to the output stream.

    Parameters
    ----------
    param : DocstringParam
        Structured representation of a parameter entry.
    parts : list[str]
        List of strings representing the final output of compose().
    rendering_style : RenderingStyle
        Rendering style to use.
    indent : str
        Indentation needed for that line.
    """
    if param.type_name:
        type_text = (
            f" {param.type_name}? " if param.is_optional else f" {param.type_name} "
        )
    else:
        type_text = " "
    if rendering_style == RenderingStyle.EXPANDED:
        text = f":param {param.arg_name}:"
        text += process_desc(param.description, rendering_style, indent)
        parts.append(text)
        if type_text[:-1]:
            parts.append(f":type {param.arg_name}:{type_text[:-1]}")
    else:
        text = f":param{type_text}{param.arg_name}:"
        text += process_desc(param.description, rendering_style, indent)
        parts.append(text)


def _append_return(
    meta: Union[DocstringReturns, DocstringYields],
    parts: list[str],
    rendering_style: RenderingStyle,
    indent: str,
) -> None:
    """Append one return/yield entry to the output stream.

    Parameters
    ----------
    meta : Union[DocstringReturns, DocstringYields]
        Structured representation of a return/yield entry.
    parts : list[str]
        List of strings representing the final output of compose().
    rendering_style : RenderingStyle
        Rendering style to use.
    indent : str
        Indentation needed for that line.
    """
    type_text = f" {meta.type_name}" if meta.type_name else ""
    key = "yields" if isinstance(meta, DocstringYields) else "returns"

    if rendering_style == RenderingStyle.EXPANDED:
        if meta.description:
            text = f":{key}:"
            text += process_desc(meta.description, rendering_style, indent)
            parts.append(text)
        if type_text:
            return_key = "rtype" if isinstance(meta, DocstringReturns) else "ytype"
            parts.append(f":{return_key}:{type_text}")
    else:
        text = f":{key}{type_text}:"
        text += process_desc(meta.description, rendering_style, indent)
        parts.append(text)


def compose(
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
    parts: list[str] = []
    append_description(docstring, parts)

    for meta in docstring.meta:
        if isinstance(meta, DocstringParam):
            _append_param(meta, parts, rendering_style, indent)
        elif isinstance(meta, (DocstringReturns, DocstringYields)):
            _append_return(meta, parts, rendering_style, indent)
        elif isinstance(meta, DocstringRaises):
            type_text = f" {meta.type_name} " if meta.type_name else ""
            text = (
                f":raises{type_text}:"
                f"{process_desc(meta.description, rendering_style, indent)}"
            )
            parts.append(text)
        else:
            text = (
                f":{' '.join(meta.args)}:"
                f"{process_desc(meta.description, rendering_style, indent)}"
            )
            parts.append(text)
    return "\n".join(parts)
