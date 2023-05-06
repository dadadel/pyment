def std_func(param="foo", bar=42):
    pass


async def async_func(param='foo', bar=42):
    return param


async def async_func2():
    raise Exception


async def async_func3(param1, param2=None):
    """
    some comment
    :param param1: my parameter 1
    :param param2: my second param
    :return: nothing
    :rtype: None
    """
    pass
