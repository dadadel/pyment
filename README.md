pyment
======

Create, update or convert docstrings in existing Python files, managing several styles.

Description
-----------

This Python (2.7+/3+, or 2.6 if installed argparser) program intends to help Python programmers to enhance inside code documentation using docstrings.
It is useful for code not well documented, or code without docstrings, or some not yet or partially documented code, or a mix of all of this :-)
It can be helpful also to haromize or change a project docstring style format.

It will parse one or several python scripts and retrieve existing docstrings.
Then, for all found functions/methods/classes, it will generate formated docstrings with parameters, default values,...

At the end, patches are generated for each file. Then, man can apply the patches to the initial scripts.
It is also possible to generate the python file with the new docstrings, or to retrieve only the docstrings...

Currently, the managed styles in input/output are javadoc, one variant of reST (re-Structured Text, used by Sphinx), numpydoc, groups (only input, Google style).

You can also configure some settings via the command line or a configuration
file.

To get further informations please refer to the [**documentation**](https://github.com/dadadel/pyment/blob/master/doc/pyment.rst).

The tool, at the time, offer to generate patches or get a list of the new docstrings (created or converted).

You can contact the developer *dadel* and speak about the project on **IRC** **Freenode**'s channel **#pyment**.

Start quickly
-------------
- get and install:

        $ git clone git@github.com:dadadel/pyment.git # or https://github.com/dadadel/pyment.git
        $ cd pyment
        $ python setup.py install

- run from the command line:

        $ pyment  myfile.py

    or

        $ pyment  my/folder/

- get help:

        $ pyment -h

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
The 1st patch was generated using the following command:

        $ pyment -f false example.py

The second using:

        $ pyment -f false -o numpydoc example.py

