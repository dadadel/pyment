pyment
======

Create, update or convert docstrings in existing Python files, managing several styles.

.. contents:: :local:

Project Status
--------------

**Test Status**

Linux: |travis|

Windows: |appveyor|


.. |travis| image:: https://travis-ci.org/dadadel/pyment.svg?branch=master
    :target: https://travis-ci.org/dadadel/pyment.svg?branch=master
    :alt: Linux tests (TravisCI)                                   

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/f9d4jps5fkf4m42h?svg=true
    :target: https://ci.appveyor.com/api/projects/status/f9d4jps5fkf4m42h?svg=true
    :alt: Windows tests (Appveyor)

|

**Supported Versions**  

.. image:: https://img.shields.io/badge/python-3.6-blue.svg
    :target: https://img.shields.io/badge/python-3.6-blue.svg  
    :alt: Supports Python36
.. image:: https://img.shields.io/badge/python-3.7-blue.svg
    :target: https://img.shields.io/badge/python-3.7-blue.svg
    :alt: Supports Python37
.. image:: https://img.shields.io/badge/python-3.8-blue.svg
    :target: https://img.shields.io/badge/python-3.8-blue.svg
    :alt: Supports Python38
.. image:: https://img.shields.io/badge/python-3.9-blue.svg
    :target: https://img.shields.io/badge/python-3.9-blue.svg
    :alt: Supports Python39

|

**Code Coverage**

.. image:: https://coveralls.io/repos/github/wagnerpeer/pyment/badge.svg?branch=enhancement%2Fcoveralls
    :target: https://coveralls.io/github/wagnerpeer/pyment?branch=enhancement%2Fcoveralls
    :alt: Test coverage (Coveralls)


Description
-----------

This Python3 program intends to help Python programmers to enhance inside code documentation using docstrings.
It is useful for code not well documented, or code without docstrings, or some not yet or partially documented code, or a mix of all of this :-)
It can be helpful also to harmonize or change a project docstring style format.

It will parse one or several python scripts and retrieve existing docstrings.
Then, for all found functions/methods/classes, it will generate formatted docstrings with parameters, default values,...

At the end, patches can be generated for each file. Then, man can apply the patches to the initial scripts.
It is also possible to update the files directly without generating patches, or to output on *stdout*. 
It is also possible to generate the python file with the new docstrings, or to retrieve only the docstrings...

Currently, the managed styles in input/output are javadoc, one variant of reST (re-Structured Text, used by Sphinx), numpydoc, google docstrings, groups (other grouped style).

You can also configure some settings via the command line or a configuration
file.

To get further information please refer to the `documentation <https://github.com/dadadel/pyment/blob/master/doc/sphinx/source/pyment.rst>`_.

The tool, at the time, offer to generate patches or get a list of the new docstrings (created or converted).

You can contact the developer *dadel* by opening a `discussion <https://github.com/dadadel/pyment/discussions/new>`_.

Start quickly
-------------
- install from Pypi

.. code-block:: sh

        $ pip install pyment

- install from sources:

.. code-block:: sh

        $ pip install git+https://github.com/dadadel/pyment.git
        or
        $ git clone https://github.com/dadadel/pyment.git
        $ cd pyment
        $ python setup.py install

- run from the command line:

.. code-block:: sh

        $ pyment  myfile.py    # will generate a patch
        $ pyment -w myfile.py  # will overwrite the file

or

.. code-block:: sh

        $ pyment  my/folder/

- get help:

.. code-block:: sh

        $ pyment -h

- run from a script:

.. code-block:: python

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

Here is a full example using Pyment to generate a patch and then apply the patch.

Let's consider a file *test.py* with following content:

.. code-block:: python

        def func(param1=True, param2: str = 'default val'):
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

Now let's use Pyment:

.. code-block:: sh

        $ pyment test.py

Using Pyment without any argument will autodetect the docstrings formats and generate a patch using the reStructured Text format.
So the previous command has generated the file *test.py.patch* with following content:

.. code-block:: patch

        # Patch generated by Pyment v0.4.0

        --- a/test.py
        +++ b/test.py
        @@ -1,20 +1,22 @@
         def func(param1=True, param2: str = 'default val'):
        -    '''Description of func with docstring groups style.
        -
        -    Params:
        -        param1 - descr of param1 that has True for default value.
        -        param2 - descr of param2
        -
        -    Returns:
        -        some value
        -
        -    Raises:
        -        keyError: raises key exception
        -        TypeError: raises type exception
        -
        -    '''
        +    """Description of func with docstring groups style.
        +
        +    :param param1: descr of param1 that has True for default value
        +    :param param2: descr of param2 (Default value = 'default val')
        +    :type param2: str
        +    :returns: some value
        +    :raises keyError: raises key exception
        +    :raises TypeError: raises type exception
        +
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
            """Description of func with docstring groups style.

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

Also refer to the files `example.py.patch <https://github.com/dadadel/pyment/blob/master/example_javadoc.py.patch>`_ or `example_numpy.py.patch <https://github.com/dadadel/pyment/blob/master/example_numpydoc.py.patch>`_ to see some other results that can be obtained processing the file `example.py <https://github.com/dadadel/pyment/blob/master/example.py>`_


Offer a coffee or a beer
------------------------

If you enjoyed this free software, and want to thank me, you can offer me some
bitcoins for a coffee, a beer, or more, I would be happy :)

Here's my address for bitcoins : 1Kz5bu4HuRtwbjzopN6xWSVsmtTDK6Kb89

