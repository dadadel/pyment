pyment
======

Create, update or change style of docstrings in existing Python files.

Description
-----------

This Python program intends to help Python programmers to enhance inside code documentation using docstrings. 
It is usefull for code not well documented, or code without docstrings, or some not yet or partially documented code.
It can be helpfull also to haromize or change a project docstring style format.

It will parse one or several python scripts and retrieve existing docstrings.
Then, for all found functions/methods/classes, it will generate formated docstrings with parameters, default values,...

At the end, patches are generated for each file. Then, man can apply the patches to the initial scripts.

Usage
-----

- from the command line:

        ./pyment.py  myfile.py

    or

        ./pyment.py  my/folder

- from a script:

        import os
        from pyment import PyComment
        
        filename = 'test.py'
        
        c = PyComment(filename)
        c.proceed()
        c.diff_to_file(os.path.basename(filename) + ".patch")

