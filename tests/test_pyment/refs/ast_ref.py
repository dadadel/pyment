# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""Some module docstring
a
bit
longer"""


def func1():
    pass


def func2():
    """SOme docstring"""
    pass


def func3():
    return 1 + 1


def func_with_params(pos, a: "annotation", b: int, c: int, *args: list, d: int = 5, e="test", **kwargs: dict) -> str:
    """_summary_.

    Parameters
    ----------
    a : _type_
        _description_
    b : int
        _description_
    c : int
        _description_ (Default value = 2)
    *args : _type_
        _description_
    d : int
        _description_ (Default value = 5)
    e : _type_
        _description_ (Default value = "test")
    **kwargs : _type_
        _description_

    Returns
    -------
    str
        _description_
    """
    pass


def func2_with_params(a: str, /, b: int, c: int = 3, d: int = 5, e="test", **kwargs) -> str:
    """Short string"""


class SomeTestClass:
    """Some docstring for that class."""

    def __init__(self, one_param=2):
        pass

SomeTestClass()
