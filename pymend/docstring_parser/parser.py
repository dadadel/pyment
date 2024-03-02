"""The main parsing routine."""

from typing import Optional

from pymend.docstring_parser import epydoc, google, numpydoc, rest
from pymend.docstring_parser.common import (
    Docstring,
    DocstringStyle,
    ParseError,
    RenderingStyle,
)

_STYLE_MAP = {
    DocstringStyle.REST: rest,
    DocstringStyle.GOOGLE: google,
    DocstringStyle.NUMPYDOC: numpydoc,
    DocstringStyle.EPYDOC: epydoc,
}


def parse(
    text: Optional[str], style: DocstringStyle = DocstringStyle.AUTO
) -> Docstring:
    """Parse the docstring into its components.

    Parameters
    ----------
    text : Optional[str]
        docstring text to parse
    style : DocstringStyle
        docstring style (Default value = DocstringStyle.AUTO)

    Returns
    -------
    Docstring
        parsed docstring representation

    Raises
    ------
    ParserError
        If none of the available module an parse the docstring
    """
    if style != DocstringStyle.AUTO:
        return _STYLE_MAP[style].parse(text)

    exc: Optional[Exception] = None
    rets: list[Docstring] = []
    for module in _STYLE_MAP.values():
        try:
            ret = module.parse(text)
        except ParseError as ex:
            exc = ex
        else:
            rets.append(ret)

    if not rets and exc:
        raise exc

    return sorted(rets, key=lambda d: (len(d.examples), len(d.meta)), reverse=True)[0]


def compose(
    docstring: Docstring,
    style: DocstringStyle = DocstringStyle.AUTO,
    rendering_style: RenderingStyle = RenderingStyle.COMPACT,
    indent: str = "    ",
) -> str:
    """Render a parsed docstring into docstring text.

    Parameters
    ----------
    docstring : Docstring
        parsed docstring representation
    style : DocstringStyle
        docstring style to render (Default value = DocstringStyle.AUTO)
    indent : str
        the characters used as indentation in the docstring string
        (Default value = '    ')
    rendering_style : RenderingStyle
        The rendering style to use. (Default value = RenderingStyle.COMPACT)

    Returns
    -------
    str
        docstring text

    Raises
    ------
    ValueError
        If no output style could be determined.
    """
    if style == DocstringStyle.AUTO:
        if docstring.style is None:
            msg = (
                "Detected docstring.style of `None` and requested style of `AUTO`.\n"
                "Either the docstring to compose has to have its style set"
                " (for example by calling `parse`) or an "
                "output style has to be provided."
            )
            raise ValueError(msg)
        style = docstring.style
    module = _STYLE_MAP[style]
    return module.compose(docstring, rendering_style=rendering_style, indent=indent)
