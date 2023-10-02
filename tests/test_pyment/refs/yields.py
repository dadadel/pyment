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

def generator() -> Iterable[str]:
    """_summary_."""
    yield "test"

def generator() -> Iterator[str]:
    """_summary_.

    Yields
    ------
    Nope
        _description_
    """
    pass

def generator() -> Generator[int, float, str]:
    """_summary_."""
    if False:
        return a
    yield b
