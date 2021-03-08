def func(): # comment with (parents):
    pass


def func0(param1): # comment with (parents):,
    """description
    :param param1: yoyo
    :returns: nothing
    """
    pass


def func1(param1: str):
    pass


def func2(param1: str) -> int:
    pass


def func3(param1: str) -> str:
    """Func 3

    :param param1: param description
    :return: the value
    """
    pass


def func4(param1: str, param2: List[int]):
    pass


def func5(param1: str, param2: List[int]) -> Dict[str,Object]:  # yet:(another) comment
    pass


def func6(param1: str, param2: Dict[str,Object]) -> str:
    """Func 6

    :param param1: the first parameter
    :type param1: str
    :param param2: the second parameter
    :returns: the message
    :rtype: str

    """
    pass


def func7(param1: str, param2: Dict[str, Object], param3: int = 12) -> str:
    pass


def func8(param1 : str, param2: list=None, param3: str = "foo", param4="bar") -> str:
    pass


def func9(param1: str,
          param2: list = None,
          param3: str = "foo") -> str:
    pass


def func10(  param1: str = "", param2='', param3=call_func('foobar')  ) :
    pass


def func11(self, param1: str, param2: Dict[str, Object], param3: OAuth2PasswordRequestForm = Depends(), param4: int = 1) -> str:
    pass


def func12(cls, param1: str, param2: Dict[str, Object], param3: int = 12) -> str:
    pass


def func13(param1, param2: Dict["str", Object], param3: int = 12) -> str:
    pass


def func14(param1=True, param2: str = 'default val'):
    '''Description of func with docstring groups style.

    Params:
        param1 - descr of param1 that has True for default value.
        param2 - descr of param2

    Returns:
        some value

    Raises:
        keyError: raises key exception
        TypeError: raises type exception

    '''
    pass

    class A:
        def method(self, param1, param2=None) -> int:
            pass

