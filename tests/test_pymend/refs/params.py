def func1():
    pass


def func2(param1):
    pass


def func3(param1, param2):
    pass


def func3(param1, param2, param3):
    pass


def func4(param1=123):
    pass


def func5(param1, param2=123):
    pass


def func6(param1, param2, param3=123):
    pass


def func7(param1, param2=None, param3=123):
    pass


def func8(param1=123, param2=+456, param3="!:@"):
    pass


def func9(param1=func1(), param2="stuff"):
    pass


def func10(param1=func1(), param2="stuff"):  # comments with (parentheses):
    pass
