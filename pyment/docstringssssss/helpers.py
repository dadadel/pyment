"""Module for helper functions for parsers and generators."""

import re
from typing import Iterable, Union


def isin_alone(elems: Iterable[str], line: str) -> bool:
    """Check if an element from a list is the only element of a string.

    Parameters
    ----------
    elems : Iterable[str]
        Iterable of elements to check
    line : str
        Line to check if it contains any element

    Returns
    -------
    bool
        Whether any element is alone in the line
    """
    return any(line.strip().lower() == e.lower() for e in elems)


def isin_start(elems: Union[Iterable[str], str], line: str) -> bool:
    """Check if an element from a list starts a string.

    Parameters
    ----------
    elems : Union[Iterable[str], str]
        Element or list of elements
    line : str
        Line to check if it contains any element

    Returns
    -------
    bool
        Whether any element is at the start of the line
    """
    elems = (elems,) if isinstance(elems, str) else elems
    return any(line.lstrip().lower().startswith(e) for e in elems)


def isin(elems: Iterable[str], line: str) -> bool:
    """Check if an element from a list is in a string.

    Parameters
    ----------
    elems : Iterable[str]
        Iterable of elements to check
    line : str
        Line to check if it contains any element

    Returns
    -------
    bool
        Whether any element is in the line
    """
    return any(e in line.lower() for e in elems)


def get_leading_spaces(data: str) -> str:
    """Get the leading space of a string if it is not empty.

    Parameters
    ----------
    data : str
        _description_

    Returns
    -------
    str
        _description_
    """
    return matches[1] if (matches := re.match(r"^(\s*)", data)) else ""
