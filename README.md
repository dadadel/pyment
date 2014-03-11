pyment
======

Create, update or convert style of docstrings in existing Python files.

Description
-----------

This Python (2.7+/3+, or 2.6 if installed argparser) program intends to help Python programmers to enhance inside code documentation using docstrings. 
It is usefull for code not well documented, or code without docstrings, or some not yet or partially documented code, or a mix of all of this :-)
It can be helpfull also to haromize or change a project docstring style format.

It will parse one or several python scripts and retrieve existing docstrings.
Then, for all found functions/methods/classes, it will generate formated docstrings with parameters, default values,...

At the end, patches are generated for each file. Then, man can apply the patches to the initial scripts.
It is also possible to generate the python file with the new docstrings, or to retrieve only the docstrings...


Example
-------
The example.py.patch was obtained with the following command:

        $ ./pyment.py example.py

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


Limitations
-----------
Note that this work is in progress! It comes with no warranty. And it don't yet offer all its intended functionalities.

Currently, no raise managed. Only javadoc, one variant of reST and a part of groups (only input) styles are managed both in input and output, but that should evolve quickly in time. 

The tool can only at the time offer to generate patches or get a list of the new docstrings.

*Note*:
It is called "groups style", the kind of GoogleDoc style, with docstrings like:

    """
    This is a groups style docs.

    Parameters:
	param1 - this is the first param
	param2 - this is a second param

    Returns:
	This is description of what is returned
    """
