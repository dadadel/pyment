Reference documentation
#######################

Pyment: the docstrings manager (creator/converter)

.. Contents::


Introduction
============

Pyment is a software allowing to create, update or convert several docstrings formats in existing Python files.
So it should help Python programmers to enhance inside code documentation using docstrings.

It should be useful for code not yet documented, not well documented, or partially documented and also to harmonize files using several docstring formats.

Pyment will then be helpful to harmonize or change a project docstring style format.

How does it work
----------------

Pyment will parse one python file or several (automatically exploring a folder and its sub-folder) and retrieve existing docstrings.
Then, for each found function/method/class, it will generate a formatted docstrings with parameters, default values,...

At the end, depending on options, original files will be overwritten or patches will be generated for each file, in which
case you just have to apply the patches.

What are the supported formats
------------------------------

Currently, the managed styles are javadoc, reST (re-Structured Text, used by Sphinx), numpydoc, google, other groups (like Google).


Customization
-------------

It is planed to provide a large customization properties. However, it is currently limited to some settings.

There are two ways to customize Pyment.

The first is using the command line options (`pyment --help`). The second is providing a configuration file as explained later in that document.


Using Pyment
============

Pyment runs using Python3.6+.

Pyment is usable as is on command line using pyment script. But it can also be used inside a Python program.

How to install
--------------

The easiest way is from Pypi using pip:

.. code-block:: sh

    pip install pyment

But to have the latest version, the better way is to install from Github:

.. code-block:: sh

    $ pip install git+https://github.com/dadadel/pyment.git
    or
    git clone git@github.com:dadadel/pyment.git # or https://github.com/dadadel/pyment.git
    cd pyment
    python setup.py install

You can also get an archive of a released version `from Github <https://github.com/dadadel/pyment/releases>`_.


How to run
----------

- To run Pyment from the command line the easiest way is to provide a Python file or a folder:

.. code-block:: sh

    pyment example.py # will generate a patch
    pyment folder/to/python/progs
    pyment -w myfile.py  # will overwrite the file
    cat myfile.py | pyment -  # will proceed the content from stdin and create a patch written on stdout
    cat myfile.py | pyment -w -  # will proceed the content from stdin and write on stdout the converted content

- To get the available options, run:

.. code-block:: sh

    pyment -h

Will provide the output:

.. code-block:: sh

    usage: pyment [-h] [-i style] [-o style] [-q quotes] [-f status] [-t]
                  [-c config] [-d] [-p status] [-v] [-w]
                  path

    Generates patches after (re)writing docstrings.

    positional arguments:
      path                  python file or folder containing python files to
                            proceed (explore also sub-folders). Use "-" to read
                            from stdin and write to stdout

    optional arguments:
      -h, --help            show this help message and exit
      -i style, --input style
                            Input docstring style in ["javadoc", "reST",
                            "numpydoc", "google", "auto"] (default autodetected)
      -o style, --output style
                            Output docstring style in ["javadoc", "reST",
                            "numpydoc", "google"] (default "reST")
      -q quotes, --quotes quotes
                            Type of docstring delimiter quotes: ''' or """
                            (default """). Note that you may escape the characters
                            using \ like \'\'\', or surround it with the opposite
                            quotes like "'''"
      -f status, --first-line status
                            Does the comment starts on the first line after the
                            quotes (default "True")
      -t, --convert         Existing docstrings will be converted but won't create
                            missing ones
      -c config, --config-file config
                            Get a Pyment configuration from a file. Note that the
                            config values will overload the command line ones.
      -d, --init2class      If no docstring to class, then move the __init__ one
      -p status, --ignore-private status
                            Don't proceed the private methods/functions starting
                            with __ (two underscores) (default "True")
      -v, --version         show program's version number and exit
      -w, --write           Don't write patches. Overwrite files instead. If used
                            with path '-' won't overwrite but write to stdout the
                            new content instead of a patch.

- To run the unit-tests:

.. code-block:: sh

    python setup.py test

- To run from a Python program:

.. code-block:: python

    import os
    from pyment import PyComment

    filename = 'test.py'

    c = PyComment(filename)
    c.proceed()
    c.diff_to_file(os.path.basename(filename) + ".patch")
    for s in c.get_output_docs():
        print(s)

Note that a documentation will be provided later. Now you can use Python introspection like: *>>> help(PyComment)*


Configuration file
==================

You can provide a configuration file to manage some settings.

Note that if you use command line parameters that are also set in the
configuration file, then the command line ones will be ignored.

The configuration parameters that you can set are:

- **first_line**

    *True or False*

Set to **True** then for each docstring, the description should start on the first
line, just after the quotes. In the other case the description will start on the
second line.

- **quotes**

    *''' or """*

The quotes used for the docstring limits.

- **output_style**

    *javadoc, reST, numpydoc, google, groups*

The output format for the docstring.

- **input_style**

    *auto, javadoc, reST, numpydoc, google, groups*

The input format for the docstring interpretation. Set to **auto** if you want
Pyment to autodetect for each docstring its format.

- **init2class**

    *True or False*

Set to **True** to move the generated docstring for __init__ to the class docstring.
If there was already a docstring for the class, then the __init__ will conserve
its docstring and the class its own.

- **convert_only**

    *True or False*

Set to **True** if you want only to convert existing docstring.
So Pyment won't create missing docstrings.

- **indent**

    *Integer value (default is 2)*

Change the amount of spaces used for indented elements.

**Todo...**

- Add other command line options
- *optional/excluded sections*

Pyment will ignore some sections (like *raises*) or will generate some sections only if there was an existing corresponding section in input docstring.


Examples
========

A full example
--------------

Here is a full example using Pyment to generate a patch and then apply the patch.

Let's consider a file *test.py* with following content:

.. code-block:: python

        def func(param1=True, param2: str = 'default val'):
            '''Description of func with docstring groups style (Googledoc).

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

Now let's use Pyment:

.. code-block:: sh

        $ pyment test.py

Using Pyment without any argument will autodetect the docstrings formats and generate a patch using the reStructured Text format.
So the previous command has generated the file *test.py.patch* with following content:

.. code-block:: diff

        # Patch generated by Pyment v0.4.0

        --- a/test.py
        +++ b/test.py
        @@ -1,20 +1,22 @@
         def func(param1=True, param2: str = 'default val'):
        -    '''Description of func with docstring groups style (Googledoc).
        +    """Description of func with docstring groups style (Googledoc).
         
        -    Params: 
        -        param1 - descr of param1 that has True for default value.
        -        param2 - descr of param2
        +    :param param1: descr of param1 that has True for default value
        +    :param param2: descr of param2 (Default value = 'default val')
        +    :type param2: str
        +    :returns: some value
        +    :raises keyError: raises key exception
        +    :raises TypeError: raises type exception
         
        -    Returns:
        -        some value
        -
        -    Raises:
        -        keyError: raises key exception
        -        TypeError: raises type exception
        -
        -    '''
        +    """
             pass
         
         class A:
        +    """ """
             def method(self, param1, param2=None) -> int:
        +        """
        +
        +        :param param1: 
        +        :param param2:  (Default value = None)
        +        :rtype: int
        +
        +        """
                 pass

Let's finally apply the patch with the following command:

.. code-block:: sh

        $ patch -p1 < test.py.patch

Now the original *test.py* was updated and its content is now:

.. code-block:: python

        def func(param1=True, param2: str = 'default val'):
            """Description of func with docstring groups style (Googledoc).

            :param param1: descr of param1 that has True for default value
            :param param2: descr of param2 (Default value = 'default val')
            :type param2: str
            :returns: some value
            :raises keyError: raises key exception
            :raises TypeError: raises type exception

            """
            pass

        class A:
            """ """
            def method(self, param1, param2=None) -> int:
                """

                :param param1: 
                :param param2:  (Default value = None)
                :rtype: int

                """
                pass


Results examples
----------------

Refer to the files `example.py.patch <https://github.com/dadadel/pyment/blob/master/example_javadoc.py.patch>`_ or `example.py.patch <https://github.com/dadadel/pyment/blob/master/example_numpydoc.py.patch>`_ to see what kind of results can be obtained.

The 1st patch was generated using the following command:

.. code-block:: sh

    pyment -f false example.py

And the second using:

.. code-block:: sh

    pyment -f false -o numpydoc example.py


Managed docstrings examples
---------------------------

There follows some examples of docstrings that can be recognized or generated.

- "javadoc" style:

.. code-block:: python

        """
        This is a javadoc style.

        @param param1: this is a first param
        @param param2: this is a second param
        @return: this is a description of what is returned
        @raise keyError: raises an exception
        """

- "reST" style (the kind managed by Sphinx):

.. code-block:: python

        """
        This is a reST style.

        :param param1: this is a first param
        :type param1: str
        :param param2: this is a second param
        :type param2: int
        :returns: this is a description of what is returned
        :rtype: bool
        :raises keyError: raises an exception
        """

- "google" style:

.. code-block:: python

        """
        This is a Google style docs.

        Args:
          param1(str): this is the first param
          param2(int, optional): this is a second param

        Returns:
            bool: This is a description of what is returned

        Raises:
            KeyError: raises an exception
        """

- "numpydoc" style:

.. code-block:: python

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

- other "groups" style:

.. code-block:: python

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

Contact/Contributing
====================

- Contact

You can an email to the developer **dadel** using daouzli AT gmail DOT com (please head your subject with *[Pyment]*).

- Contribute

Concerning contributing, note that the development is in early steps, and the global code arrangement can change, especially concerning making easier to add new format support.
However you can contribute by opening issues, proposing pull requests, or contacting directly the developer.

The tests are unfortunately not good enough, so you can contribute in that field, that would be really great!
An other useful way to contribute should be to create a plugin for you favorite IDE.
You can also find in the code some TODO/FIXME, not always up-to-date.

- Donate

If you enjoyed this free software, and want to donate you can give me some bitcoins, I would be happy :)

Here's my address for bitcoins : 1Kz5bu4HuRtwbjzopN6xWSVsmtTDK6Kb89
