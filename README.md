pyment
======

Create, update or convert docstrings in existing Python files, managing several styles.

Description
-----------

This Python (2.7+/3+, or 2.6 if installed argparser) program intends to help Python programmers to enhance inside code documentation using docstrings.
It is usefull for code not well documented, or code without docstrings, or some not yet or partially documented code, or a mix of all of this :-)
It can be helpfull also to haromize or change a project docstring style format.

It will parse one or several python scripts and retrieve existing docstrings.
Then, for all found functions/methods/classes, it will generate formated docstrings with parameters, default values,...

At the end, patches are generated for each file. Then, man can apply the patches to the initial scripts.
It is also possible to generate the python file with the new docstrings, or to retrieve only the docstrings...

Currently, the managed styles (input/output) are javadoc, one variant of reST (re-Structured Text, used by Sphinx), numpydoc and groups (only input, style like used by Google).

The tool can only at the time offer to generate patches or get a list of the new docstrings.

You can contact the developer *dadel* and speak about the project on **IRC** **Freenode**'s channel **#pyment**.

Usage
-----
- get and install:

        $ git clone git@github.com:dadadel/pyment.git # or https://github.com/dadadel/pyment.git
        $ cd pyment
        $ python setup.py install

- run from the command line:

        pyment  myfile.py

    or

        pyment  my/folder/

- get help:

        $ pyment -h

        usage: pyment [-h] [-i style] [-o style] [-v] path

        Generates patches after (re)writing docstrings.

        positional arguments:
          path                  python file or folder containing python files to
                                proceed (explore also sub-folders)

        optional arguments:
          -h, --help            show this help message and exit
          -i style, --input style
                                Input docstring style in ["javadoc", "reST",
                                "numpydoc", "auto"] (default autodetected)
          -o style, --output style
                                Output docstring style in ["javadoc", "reST"] (default
                                "reST")
          -v, --version         show program's version number and exit

- running tests:

        $ python setup.py test

- run from a script:

        import os
        from pyment import PyComment

        filename = 'test.py'

        c = PyComment(filename)
        c.proceed()
        c.diff_to_file(os.path.basename(filename) + ".patch")
        for s in c.get_output_docs():
            print(s)

Example
-------
See the [example.py.patch](https://github.com/dadadel/pyment/blob/master/example.py.patch) or [example.py.patch](https://github.com/dadadel/pyment/blob/master/example_numpy.py.patch) file to see what kind of results can be obtained.
Such a patch is generated using the following command:

        $ pyment example.py


Examples of managed docstrings:

- "javadoc" style:

        """
        This is a javadoc style.

        @param param1: this is a first param
        @param param2: this is a second param
        @return: this is a description of what is returned
        @raise keyError: raises an exception
        """

- "reST" style (the kind managed by Sphinx):

        """
        This is a reST style.

        :param param1: this is a first param
        :param param2: this is a second param
        :returns: this is a description of what is returned
        :raises keyError: raises an exception
        """

- "groups" style (the kind used by Google):

        """
        This is a groups style docs.

        Parameters:
            param1 - this is the first param
            param2 - this is a second param

        Returns:
            This is a description of what is returned

        Raises:
            KeyError - raises an exception
        """

- "numpydoc" style:
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
