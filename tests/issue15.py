def func(param1=True, param2='default val'):
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
    def method(self, param1, param2=None):
        pass

if __name__ == "__main__":
    import os
    from pyment import PyComment

    filename = __file__
    print filename

    c = PyComment(filename)
    c.proceed()
    c.diff_to_file(os.path.basename(filename) + ".patch")
    for s in c.get_output_docs():
        print(s)

