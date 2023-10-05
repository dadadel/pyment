"""The main parsing routine."""

import inspect
from typing import Optional

from pyment.docstring_parser import epydoc, google, numpydoc, rest
from pyment.docstring_parser.attrdoc import add_attribute_docstrings
from pyment.docstring_parser.common import (
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
    text : str
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
    rets = []
    for module in _STYLE_MAP.values():
        try:
            ret = module.parse(text)
        except ParseError as ex:
            exc = ex
        else:
            rets.append(ret)

    if not rets and exc:
        raise exc

    return sorted(rets, key=lambda d: len(d.meta), reverse=True)[0]


def parse_from_object(
    obj: object,
    style: DocstringStyle = DocstringStyle.AUTO,
) -> Docstring:
    """Parse the object's docstring(s) into its components.

    The object can be anything that has a ``__doc__`` attribute. In contrast to
    the ``parse`` function, ``parse_from_object`` is able to parse attribute
    docstrings which are defined in the source code instead of ``__doc__``.

    Currently only attribute docstrings defined at class and module levels are
    supported. Attribute docstrings defined in ``__init__`` methods are not
    supported.

    When given a class, only the attribute docstrings of that class are parsed,
    not its inherited classes. This is a design decision. Separate calls to
    this function should be performed to get attribute docstrings of parent
    classes.

    Parameters
    ----------
    obj : object
        object from which to parse the docstring(s)
    style : DocstringStyle
        docstring style (Default value = DocstringStyle.AUTO)

    Returns
    -------
    Docstring
        parsed docstring representation
    """
    docstring = parse(obj.__doc__, style=style)

    if inspect.isclass(obj) or inspect.ismodule(obj):
        add_attribute_docstrings(obj, docstring)

    return docstring


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
        _description_ (Default value = RenderingStyle.COMPACT)

    Returns
    -------
    str
        docstring text
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
