def func1(param1, param2='default val'):
    '''Description of func with docstring javadoc style.

    @param param1: descr of param
    @type param1: type
    @return: some value
    @raise KeyError: raises a key exception

    '''
    pass

def func2(param1, param2='default val2'):
    '''Description of func with docstring reST style.

    :param param1: descr of param
    :type param1: type
    :returns: some value
    :raises keyError: raises exception

    '''
    pass

def func3(param1, param2='default val'):
    '''Description of func with docstring groups style.

    Params: 
        param1 - descr of param

    Returns:
        some value

    Raises:
        keyError: raises key exception
        TypeError: raises type exception

    '''
    pass

class SomeClass(object):
    '''My class.
    '''
    def method(self, prm):
        '''description'''
        pass

    def method2(self, prm1, prm2='defaultprm'):
        pass
