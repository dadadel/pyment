"""_summary_."""
class A:
    def __init__(self):
        """_summary_."""
        self._x = None
        self.test1 = "test"
        self.test2 = None
        self.test2 = 1
        self.test1 = "a"
        self.test3 = self.test4 = None

    @property
    def x(self) -> str | None:
        """I'm the 'x' property.

        Returns
        -------
        str | None
            _description_
        """
        return self._x

    @x.setter
    def x(self, value):
        """_summary_.

        Parameters
        ----------
        value : _type_
            _description_
        """
        self._x = value

    @staticmethod
    def a(self, a):
        """_summary_.

        Parameters
        ----------
        a : _type_
            _description_
        """
        pass

    @classmethod
    def b(self, b):
        """_summary_.

        Parameters
        ----------
        b : _type_
            _description_
        """
        pass

    def c(self, c):
        """_summary_.

        Parameters
        ----------
        c : _type_
            _description_
        """
        pass

    def d(self, pos, /, a: "annotation", b: int, c: int, *args: list, d: int = 5, e="test", **kwargs: dict):
        """_summary_.

        Parameters
        ----------
        pos : _type_
            _description_
        a : 'annotation'
            _description_
        b : int
            _description_
        c : int
            _description_
        *args : list
            _description_
        d : int
            _description_ (Default value = 5)
        e : _type_
            _description_ (Default value = 'test')
        **kwargs : dict
            _description_
        """
        pass

class B:
    """_summary_."""
    def __init__(self):
        """_summary_."""
        self._x = None
        self.test1 = "test"
        self.test2 = None
        self.test2 = 1
        self.test1 = "a"
        self.test3 = self.test4 = None

    @property
    def x(self) -> str | None:
        """I'm the 'x' property.

        Returns
        -------
        str | None
            _description_
        """
        return self._x

    @x.setter
    def x(self, value):
        """_summary_.

        Parameters
        ----------
        value : _type_
            _description_
        """
        self._x = value

    @staticmethod
    def a(self, a):
        """_summary_.

        Parameters
        ----------
        a : _type_
            _description_
        """
        pass

    @classmethod
    def b(self, b):
        """_summary_.

        Parameters
        ----------
        b : _type_
            _description_
        """
        pass

    def c(self, c):
        """_summary_.

        Parameters
        ----------
        c : _type_
            _description_
        """
        pass

class C:
    """_summary_.

    Attributes
    ----------
    a
        some description
    b : int
    """
    def __init__(self):
        """_summary_."""
        self.a = None
        self.b = None
        self.c = None