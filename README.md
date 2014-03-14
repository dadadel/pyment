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

Currently, the managed styles (input/output) are javadoc, one variant of reST (restructured text, used by Sphinx) and groups (only input, style like used by Google). 

The tool can only at the time offer to generate patches or get a list of the new docstrings.

Example
-------
See the **example.py.patch** file to see what kind of result can be obtained.
That patch was obtained using the following command:

        $ ./pyment.py example.py

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

Usage
-----
- get help:

        $ ./pyment.py -h

        usage: pyment.py [-h] [-i style] [-o style] [-v] path
        
        Generates patches after (re)writing docstrings.

        positional arguments:
          path                  python file or folder containing python files to
                                proceed
        
        optional arguments:
          -h, --help            show this help message and exit
          -i style, --input style
                                Input docstring style in ["javadoc", "reST", "groups", "auto"]
                                (default autodetected)
          -o style, --output style
                                Output docstring style in ["javadoc", "reST"] (default "reST")
          -v, --version         show program's version number and exit
        
- run from the command line:

        ./pyment.py  myfile.py

    or

        ./pyment.py  my/folder/

- run from a script:

        import os
        from pyment import PyComment
        
        filename = 'test.py'
        
        c = PyComment(filename)
        c.proceed()
        c.diff_to_file(os.path.basename(filename) + ".patch")
        for s in c.get_output_docs():
            print(s)

