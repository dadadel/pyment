"""_summary_."""
def generator() -> Tuple[int, int, str]:
    """_summary_.

    Returns
    -------
    a : int
        Something
    b : int
        Something else
    
    Yields
    ------
    x : int
        _description_
    z : str
        desc.
    """
    if False:
        return a, b, c
    yield x, y, z


def generator() -> str:
    """_summary_.

    Returns
    -------
    _type_
        desc
    """
    if False:
        return a
    yield b

def generator() -> str:
    """_summary_.

    Returns
    -------
    _type_
        desc
    """
    return a
