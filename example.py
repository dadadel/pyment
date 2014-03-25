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

    def method_numpy(self):
        """
        My numpydoc description of a kind
        of very exhautive numpydoc format docstring.

        Parameters
        ----------
        first : array_like
            the 1st param name `first`
        second :
            the 2nd param
        third : {'value', 'other'}, optional
            the 3rd param, by default 'value'

        Returns
        -------
        string
            a value in a string

        Raises
        ------
        KeyError
            when a key error
        OtherError
            when an other error

        See Also
        --------
        a_func : linked (optional), with things to say
                 on several lines
        some blabla

        Note
        ----
        Some informations.

        Some maths also:
        .. math:: f(x) = e^{- x}

        References
        ----------
        Biblio with cited ref [1]_. The ref can be cited in Note section.

        .. [1] Adel Daouzli, Sylvain Saïghi, Michelle Rudolph, Alain Destexhe,
           Sylvie Renaud: Convergence in an Adaptive Neural Network:
           The Influence of Noise Inputs Correlation. IWANN (1) 2009: 140-148

        Examples
        --------
        This is example of use
        >>> print "a"
        a

        """
        pass
