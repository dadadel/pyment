pymend
======

Create, update or convert docstrings in existing Python files, managing several styles.

.. contents:: :local:

Project Status
--------------

**Test Status**


[![Build](https://github.com/JanEricNitschke/pymend/actions/workflows/build.yml/badge.svg)](https://github.com/JanEricNitschke/pymend/workflows/build.yml) [![Documentation Status](https://readthedocs.org/projects/pymend/badge/?version=latest)](https://pymend.readthedocs.io/en/latest/?badge=latest)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://github.com/JanEricNitschke/pymend/blob/main/LICENSE) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json)](https://github.com/charliermarsh/ruff) [![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/) [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

**Supported Versions**

.. image:: https://img.shields.io/badge/python-3.9-blue.svg
    :target: https://img.shields.io/badge/python-3.9-blue.svg
    :alt: Supports Python39
.. image:: https://img.shields.io/badge/python-3.10-blue.svg
    :target: https://img.shields.io/badge/python-3.10-blue.svg
    :alt: Supports Python310
.. image:: https://img.shields.io/badge/python-3.11-blue.svg
    :target: https://img.shields.io/badge/python-3.11-blue.svg
    :alt: Supports Python311
.. image:: https://img.shields.io/badge/python-3.12-blue.svg
    :target: https://img.shields.io/badge/python-3.12-blue.svg
    :alt: Supports Python312

|

.. **Code Coverage**

.. .. image:: https://coveralls.io/repos/github/wagnerpeer/pymend/badge.svg?branch=enhancement%2Fcoveralls
..     :target: https://coveralls.io/github/wagnerpeer/pymend?branch=enhancement%2Fcoveralls
..     :alt: Test coverage (Coveralls)


Description
-----------

Command-line program to generate, update or transform docstrings python source code.

The app will parse the requested source files for docstrings as well as function signatures
and class bodies.

This information is combined to build up complete docstrings for every function and class
including place holders for types and descriptions where none could be found elsewhere.

The output format of the docstrings can be chosen between google, numpy, reST and epydoc.
This means that the tool can also be used to transform docstrings in the file from one format into another.

Note however that not all section types are supported for all docstring styles.

Partially because they have not been added yet, but also because not every style officially supports the sections
from all others.

To get further information please refer to the `documentation <https://github.com/dadadel/pymend/blob/master/doc/sphinx/source/pymend.rst>`_.

The tool offers the choice between generating patch files or directly overwriting the python source files.


Start quickly
-------------
- install from PyPi

.. code-block:: sh

        $ pip install pymend

- install from sources:

.. code-block:: sh

        $ pip install git+https://github.com/JanEricNitschke/pymend.git
        or
        $ git clone https://github.com/JanEricNitschke/pymend.git
        $ cd pymend
        $ python setup.py install

- run from the command line:

.. code-block:: sh

        $ pymend  myfile.py    # will generate a patch
        $ pymend -w myfile.py  # will overwrite the file

or

.. code-block:: sh

        $ pymend  my/folder/

- get help:

.. code-block:: sh

        $ pymend -h

- run from a script:


Example
-------

TODO


Acknowledgements
----------------

This project was inspired by and is originally based upon [pyment](https://github.com/dadadel/pyment/).
The intended functionality as well as the main entry point remain largerly unchanged.
However additional functionality has been added in the form of ast traversal for extracting
function and class information.

The docstring parsing has been replaced completely with code taken from the awesome [docstring_parser](https://github.com/rr-/docstring_parser)
project, specifically [this fork](https://github.com/jsh9/docstring_parser_fork).

So far only minor modifications have been made to the docstring parsing functionality. Mainly the addition of the "Methods" section
for numpydoc style docstrings. Additionally the the code has been linted as well as type hinted.
