def foo():
    __doc__ = """\
    Foo"""


def bar(param):
    r"""this is a docstring
    """


def foobar():
    u"""this is a docstring
    """


def no_docs():
    something = '''bla bla bla'''
