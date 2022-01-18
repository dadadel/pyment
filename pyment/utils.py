import re


def isin_alone(elems, line):
    """Check if an element from a list is the only element of a string.

    :type elems: list
    :type line: str

    """
    return line.strip().lower() in set(e.lower() for e in elems)


def isin_start(elems, line):
    """Check if an element from a list starts a string.

    :type elems: list
    :type line: str

    """
    elems = [elems] if type(elems) is not list else elems
    return any(line.lstrip().lower().startswith(e) for e in elems)


def isin(elems, line):
    """Check if an element from a list is in a string.

    :type elems: list
    :type line: str

    """
    return any(e in line.lower() for e in elems)


def get_leading_spaces(data):
    """Get the leading space of a string if it is not empty

    :type data: str

    """
    m = re.match(r"^(\s*)", data)
    return m.group(1) if m else ""
