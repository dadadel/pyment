pymend
======

Create, update or convert docstrings in existing Python files, managing
several styles.

Project Status
--------------

**Test Status**

|Build| |Documentation Status|

|License: GPL v3| |Code style: black| |linting: pylint| |Ruff| |Checked
with pyright| |pre-commit|

**Supported Versions**

|Supports Python39|
|Supports Python310|
|Supports Python311|
|Supports Python312|


.. **Code Coverage**

.. .. image:: https://coveralls.io/repos/github/wagnerpeer/pymend/badge.svg?branch=enhancement%2Fcoveralls
..       :target: https://coveralls.io/github/wagnerpeer/pymend?branch=enhancement%2Fcoveralls
..       :alt: Test coverage (Coveralls)

Description
-----------

Command-line program to generate, update or transform docstrings python
source code.

The app will parse the requested source files for docstrings as well as
function signatures and class bodies.

This information is combined to build up complete docstrings for every
function and class including place holders for types and descriptions
where none could be found elsewhere.

The output format of the docstrings can be chosen between google, numpy,
reST and epydoc. This means that the tool can also be used to transform
docstrings in the file from one format into another.

Note however that not all section types are supported for all docstring
styles.

Partially because they have not been added yet, but also because not
every style officially supports the sections from all others.

To get further information please refer to the
`documentation <https://github.com/dadadel/pymend/blob/master/doc/sphinx/source/pymend.rst>`__.

The tool offers the choice between generating patch files or directly
overwriting the python source files.

Start quickly
-------------

-  install from PyPi

.. code:: sh

   $ pip install pymend

-  install from sources:

.. code:: sh

   $ pip install git+https://github.com/JanEricNitschke/pymend.git
   or
   $ git clone https://github.com/JanEricNitschke/pymend.git
   $ cd pymend
   $ python setup.py install

-  run from the command line:

.. code:: sh

   $ pymend  myfile.py    # will generate a patch
   $ pymend -w myfile.py  # will overwrite the file

or

.. code:: sh

   $ pymend  my/folder/

-  get help:

.. code:: sh

   $ pymend -h

Example
-------

TODO

Pre-commit
----------

To use pymend in a `pre-commit <https://pre-commit.com/>`__ hook just
add the following to your ``.pre-commit-config.yaml``

.. code:: yaml

   repos:
   -   repo: https://github.com/JanEricNitschke/pymend
       rev: "v1.0.0"
       hooks:
       -   id: pymend
           language: python
           args: ["--write", "--output=numpydoc"]

Acknowledgements
----------------

This project was inspired by and is originally based upon
`pyment <https://github.com/dadadel/pyment/>`__. The intended
functionality as well as the main entry point remain largerly unchanged.
However additional functionality has been added in the form of ast
traversal for extracting function and class information.

The docstring parsing has been replaced completely with code taken from
the awesome
`docstring_parser <https://github.com/rr-/docstring_parser>`__ project,
specifically `this
fork <https://github.com/jsh9/docstring_parser_fork>`__.

So far only minor modifications have been made to the docstring parsing
functionality. Mainly the addition of the “Methods” section for numpydoc
style docstrings. Additionally the the code has been linted as well as
type hinted.

.. |Build| image:: https://github.com/JanEricNitschke/pymend/actions/workflows/build.yaml/badge.svg
   :target: https://github.com/JanEricNitschke/pymend/workflows/build.yaml
.. |Documentation Status| image:: https://readthedocs.org/projects/pymend/badge/?version=latest
   :target: https://pymend.readthedocs.io/en/latest/?badge=latest
.. |License: GPL v3| image:: https://img.shields.io/badge/License-GPLv3-blue.svg
   :target: https://github.com/JanEricNitschke/pymend/blob/main/LICENSE
.. |Code style: black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
.. |linting: pylint| image:: https://img.shields.io/badge/linting-pylint-yellowgreen
   :target: https://github.com/pylint-dev/pylint
.. |Ruff| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json
   :target: https://github.com/charliermarsh/ruff
.. |Checked with pyright| image:: https://microsoft.github.io/pyright/img/pyright_badge.svg
   :target: https://microsoft.github.io/pyright/
.. |pre-commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit
   :target: https://github.com/pre-commit/pre-commit
.. |Supports Python39| image:: https://img.shields.io/badge/python-3.9-blue.svg
   :target: https://img.shields.io/badge/python-3.9-blue.svg
.. |Supports Python310| image:: https://img.shields.io/badge/python-3.10-blue.svg
   :target: https://img.shields.io/badge/python-3.10-blue.svg
.. |Supports Python311| image:: https://img.shields.io/badge/python-3.11-blue.svg
   :target: https://img.shields.io/badge/python-3.11-blue.svg
.. |Supports Python312| image:: https://img.shields.io/badge/python-3.12-blue.svg
   :target: https://img.shields.io/badge/python-3.12-blue.svg
