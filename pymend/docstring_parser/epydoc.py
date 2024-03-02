"""Epyoc-style docstring parsing.

.. seealso:: http://epydoc.sourceforge.net/manual-fields.html
"""

import inspect
import re
from typing import NamedTuple, Optional

from .common import (
    Docstring,
    DocstringMeta,
    DocstringParam,
    DocstringRaises,
    DocstringReturns,
    DocstringStyle,
    DocstringYields,
    ParseError,
    RenderingStyle,
    append_description,
    clean_str,
    split_description,
)


class SectionPattern(NamedTuple):
    """Patterns for docstring sections."""

    param: re.Pattern[str]
    raises: re.Pattern[str]
    returns: re.Pattern[str]
    meta: re.Pattern[str]


class SectionMatch(NamedTuple):
    """Matches of docstring sections."""

    param: Optional[re.Match[str]]
    raises: Optional[re.Match[str]]
    returns: Optional[re.Match[str]]
    meta: Optional[re.Match[str]]


def _get_matches_for_chunk(chunk: str, patterns: SectionPattern) -> SectionMatch:
    """Apply a search for each pattern to the chunk.

    Parameters
    ----------
    chunk : str
        Chunk to match the patterns against.
    patterns : SectionPattern
        Collection of regex patterns to match against the chunk.

    Returns
    -------
    SectionMatch
        Tuple of matches of the patterns against the chunk.
    """
    return SectionMatch(
        param=re.search(patterns.param, chunk),
        raises=re.search(patterns.raises, chunk),
        returns=re.search(patterns.returns, chunk),
        meta=re.search(patterns.meta, chunk),
    )


class StreamToken(NamedTuple):
    """One entry of the stream list."""

    base: str
    key: str
    args: list[str]
    desc: str


def _tokenize(
    meta_chunk: str,
    patterns: SectionPattern,
) -> list[StreamToken]:
    """Return the tokenized stream according to the regex patterns.

    Parameters
    ----------
    meta_chunk : str
        Chunk to tokenize.
    patterns : SectionPattern
        Collection of patterns for different sections.

    Returns
    -------
    list[StreamToken]
        (base, key, args, desc)
        base: Literal['param', 'raise', 'return', 'meta']
        key: str:
        args: List[str]
        desc: str: Description

    Raises
    ------
    ParseError
        If none of the patterns match against the chunk.
    ParseError
        If we match a section in the general meta case that should have already
        been matched in a specific section.
    """
    stream: list[StreamToken] = []
    for chunk_match in re.finditer(r"(^@.*?)(?=^@|\Z)", meta_chunk, flags=re.S | re.M):
        chunk = chunk_match.group(0)
        if not chunk:
            continue

        matches = _get_matches_for_chunk(chunk, patterns)

        match = matches.param or matches.raises or matches.returns or matches.meta
        if not match:
            msg = f'Error parsing meta information near "{chunk}".'
            raise ParseError(msg)

        if matches.param:
            base = "param"
            key: str = match.group(1)
            args = [match.group(2).strip()]
        elif matches.raises:
            base = "raise"
            key: str = match.group(1)
            args = [] if match.group(2) is None else [match.group(2).strip()]
        elif matches.returns:
            base = "return" if match.group(1) in ("return", "rtype") else "yield"
            key: str = match.group(1)
            args = []
        else:
            base = "meta"
            key: str = match.group(1)
            token = clean_str(match.group(2).strip())
            args = [] if token is None else re.split(r"\s+", token)

            # Make sure we didn't match some existing keyword in an incorrect
            # way here:
            if key in {
                "param",
                "keyword",
                "type",
                "return",
                "rtype",
                "yield",
                "ytype",
            }:
                msg = f'Error parsing meta information near "{chunk}".'
                raise ParseError(msg)

        desc = chunk[match.end() :].strip()
        if "\n" in desc:
            first_line, rest = desc.split("\n", 1)
            desc = first_line + "\n" + inspect.cleandoc(rest)
        stream.append(StreamToken(base, key, args, desc))
    return stream


def _combine_params(stream: list[StreamToken]) -> dict[str, dict[str, Optional[str]]]:
    """Group the list of tokens into sections based on section and information..

    Parameters
    ----------
    stream : list[StreamToken]
        List of tokens to group into dict.

    Returns
    -------
    dict[str, dict[str, Optional[str]]]
        Dictionary grouping parsed param sections
        by section (param name, "return", "yield") and
        information they represent (type_name, description)
    """
    params: dict[str, dict[str, Optional[str]]] = {}
    for base, key, args, desc in stream:
        if base not in ["param", "return", "yield"]:
            continue  # nothing to do
        arg_name = args[0] if base == "param" else base
        info = params.setdefault(arg_name, {})
        info_key = "type_name" if "type" in key else "description"
        info[info_key] = desc
    return params


def _add_meta_information(
    stream: list[StreamToken],
    params: dict[str, dict[str, Optional[str]]],
    ret: Docstring,
) -> None:
    """Add the meta information into the docstring instance.

    Parameters
    ----------
    stream : list[StreamToken]
        Stream of tokens of the string-
    params : dict[str, dict[str, Optional[str]]]
        Grouped information about each section.
    ret : Docstring
        Docstring instance to add the information to.

    Raises
    ------
    ParseError
        If an unexpected section is encountered.
    """
    is_done: dict[str, bool] = {}
    for token in stream:
        if token.base == "param" and not is_done.get(token.args[0], False):
            (arg_name,) = token.args
            info = params[arg_name]
            type_name = info.get("type_name")

            if type_name and type_name.endswith("?"):
                is_optional = True
                type_name = type_name[:-1]
            else:
                is_optional = False

            match = re.match(r".*defaults to (.+)", token.desc, flags=re.DOTALL)
            default = match[1].rstrip(".") if match else None

            meta_item = DocstringParam(
                args=[token.key, arg_name],
                description=info.get("description"),
                arg_name=arg_name,
                type_name=type_name,
                is_optional=is_optional,
                default=default,
            )
            is_done[arg_name] = True
        elif token.base == "return" and not is_done.get("return", False):
            info = params["return"]
            meta_item = DocstringReturns(
                args=[token.key],
                description=info.get("description"),
                type_name=info.get("type_name"),
                is_generator=False,
            )
            is_done["return"] = True
        elif token.base == "yield" and not is_done.get("yield", False):
            info = params["yield"]
            meta_item = DocstringYields(
                args=[token.key],
                description=info.get("description"),
                type_name=info.get("type_name"),
                is_generator=True,
            )
            is_done["yield"] = True
        elif token.base == "raise":
            (type_name,) = token.args or (None,)
            meta_item = DocstringRaises(
                args=[token.key, *token.args],
                description=token.desc,
                type_name=type_name,
            )
        elif token.base == "meta":
            meta_item = DocstringMeta(
                args=[token.key, *token.args],
                description=token.desc,
            )
        else:
            arg_key = token.args[0] if token.args else token.base
            if not is_done.get(arg_key, False):
                msg = (
                    "Error building meta information. "
                    f"Encountered unexpected section {arg_key}."
                )
                raise ParseError(msg)
            continue  # don't append

        ret.meta.append(meta_item)


def parse(text: Optional[str]) -> Docstring:
    """Parse the epydoc-style docstring into its components.

    Parameters
    ----------
    text : Optional[str]
        docstring to parse

    Returns
    -------
    Docstring
        parsed docstring
    """
    ret = Docstring(style=DocstringStyle.EPYDOC)
    if not text:
        return ret

    text = inspect.cleandoc(text)
    if match := re.search("^@", text, flags=re.M):
        desc_chunk = text[: match.start()]
        meta_chunk = text[match.start() :]
    else:
        desc_chunk = text
        meta_chunk = ""

    split_description(ret, desc_chunk)

    patterns = SectionPattern(
        param=re.compile(r"(param|keyword|type)(\s+[_A-z][_A-z0-9]*\??):"),
        raises=re.compile(r"(raise)(\s+[_A-z][_A-z0-9]*\??)?:"),
        returns=re.compile(r"(return|rtype|yield|ytype):"),
        meta=re.compile(r"([_A-z][_A-z0-9]+)((\s+[_A-z][_A-z0-9]*\??)*):"),
    )

    # tokenize
    stream = _tokenize(meta_chunk, patterns)

    # Combine type_name, arg_name, and description information
    params = _combine_params(stream)

    _add_meta_information(stream, params, ret)

    return ret


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
        the characters used as indentation in the
        docstring string (Default value = '    ')

    Returns
    -------
    str
        docstring text
    """

    def process_desc(desc: Optional[str], *, is_type: bool) -> str:
        """Process a description section.

        Parameters
        ----------
        desc : Optional[str]
            Description to process
        is_type : bool
            Whether the description represent type information.

        Returns
        -------
        str
            The properly rendered description information.
        """
        if not desc:
            return ""

        if rendering_style == RenderingStyle.EXPANDED or (
            rendering_style == RenderingStyle.CLEAN and not is_type
        ):
            (first, *rest) = desc.splitlines()
            return "\n".join(["\n" + indent + first] + [indent + line for line in rest])

        (first, *rest) = desc.splitlines()
        return "\n".join([f" {first}"] + [indent + line for line in rest])

    parts: list[str] = []
    append_description(docstring, parts)

    for meta in docstring.meta:
        if isinstance(meta, DocstringParam):
            if meta.type_name:
                type_name = f"{meta.type_name}?" if meta.is_optional else meta.type_name
                text = f"@type {meta.arg_name}:"
                text += process_desc(type_name, is_type=True)
                parts.append(text)
            text = (
                f"@param {meta.arg_name}:"
                f"{process_desc(meta.description, is_type=False)}"
            )
            parts.append(text)
        elif isinstance(meta, (DocstringReturns, DocstringYields)):
            (arg_key, type_key) = (
                ("yield", "ytype")
                if isinstance(meta, DocstringYields)
                else ("return", "rtype")
            )
            if meta.type_name:
                text = f"@{type_key}:{process_desc(meta.type_name, is_type=True)}"
                parts.append(text)
            if meta.description:
                text = f"@{arg_key}:{process_desc(meta.description, is_type=False)}"
                parts.append(text)
        elif isinstance(meta, DocstringRaises):
            text = f"@raise {meta.type_name}:" if meta.type_name else "@raise:"
            text += process_desc(meta.description, is_type=False)
            parts.append(text)
        else:
            text = f'@{" ".join(meta.args)}:'
            text += process_desc(meta.description, is_type=False)
            parts.append(text)
    return "\n".join(parts)
