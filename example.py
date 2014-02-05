def func1(parameter='default val'):
    '''Description of func with docstring javadoc style.

    @param parameter: descr of param
    @type parameter: type
    @return: some value

    '''
    pass

def func2(parameter='default val2'):
    '''Description of func with docstring reST style.

    :param parameter: descr of param
    :type parameter: type
    :return: some value

    '''
    pass

def func3(myparam='default val'):
    '''Description of func with docstring groups style.

    Params: 
        myparam - descr of param

    Returns:
        some value

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
