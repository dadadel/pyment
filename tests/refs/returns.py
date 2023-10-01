def my_func(param0, param01: int, param1: str = "Some value", param2: List[str] = {}):
    """_summary_.

    Args:
        param0 (_type_): _description_
        param01 (int): _description_
        param1 (str, optional): _description_. Defaults to "Some value".
        param2 (List[str], optional): _description_. Defaults to {}.
    """
    pass


def my_single_return_func1() -> str:
    """_summary_.

    Returns
    -------
    int
        Wrong
    """
    pass


def my_single_return_func2():
    """_summary_.

    Returns
    -------
    int
        Wrong
    """
    pass


def my_single_return_func3():
    """_summary_.

    Returns
    -------

        test
    """
    pass


def my_single_return_func4():
    pass

def my_single_return_func5():
    """Existing docstring."""
    pass

def my_single_return_func6() -> None:
    """Existing docstring."""
    pass

def my_func1(param0, param01: int):
    """_summary_.

    Args:
        param0 (_type_): _description_
        param01 (int): _description_
    """
    pass


def my_multi_return_func() -> Tuple[int, str, bool]:
    """_summary_.

    Returns
    -------
    x :
        Some integer
    y : str
        Some string
    z : bool
        Some bool
    """
    pass
