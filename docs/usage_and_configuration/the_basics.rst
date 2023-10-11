The basics
==========

Foundational knowledge on using and configuring pymend.

*PyMend* is a well-behaved Unix-style command-line tool:

- it does nothing if it finds no sources to format;
- it only outputs messages to users on standard error;
- exits with code 0 unless an internal error occurred or a CLI option prompted it.

Usage
-----

To get started right away with sensible defaults:

.. code-block:: sh

    pymend {source_file}


You can run *PyMend* as a package if running it as a script doesn't work:

.. code-block:: sh

        python -m pymend {source_file}

Command line options
^^^^^^^^^^^^^^^^^^^^

The CLI options of *PyMend* can be displayed by running :code:`pymend --help`. All options are
also covered in more detail below.

Note that all command-line options listed above can also be configured using a
:code:`pyproject.toml` file (more on that below).

:code:`-o`, :code:`--output-style`
""""""""""""""""""""""""""""""""""

The output style used for the docstrings from pymend.
Can chose between `numpydoc <https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard>`__,
`google <https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings>`__,
`reST <https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html>`__ and `epydoc <https://epydoc.sourceforge.net/manual-epytext.html>`__

:code:`-i`, :code:`--input-style`
"""""""""""""""""""""""""""""""""
The style that the existing docstrings in the file are written in.
This supports the same options as :code:`--output-style` as well as `auto` which will
try all available options and chose the one that fit best.

So if you already know the style then setting this option speed up the analysis.
It also help with handling edge cases where elements from multiple styles
are present in the docstring. This can be the case in descriptions or examples.

:code:`--exclude`
"""""""""""""""""

A regular expression that matches files and directories that should be excluded on
recursive searches. An empty value means no paths are excluded. Use forward slashes for
directories on all platforms (Windows, too).

:code:`--extend-exclude`
""""""""""""""""""""""""

Like :code:`--exclude`, but adds additional files and directories on top of the excluded ones.
Useful if you simply want to add to the default.

:code:`-q`, :code:`--quiet`
"""""""""""""""""""""""""""

Passing :code:`-q` / :code:`--quiet` will cause *PyMend* to stop emitting all non-critical output.
Error messages will still be emitted (which can silenced by :code:`2>/dev/null`).


:code:`-v`, :code:`--verbose`
"""""""""""""""""""""""""""""

Passing :code:`-v` / :code:`--verbose` will cause *PyMend* to also emit messages about files that
were not changed or were ignored due to exclusion patterns. If *PyMend* is using a
configuration file, a blue message detailing which one it is using will be emitted.

:code:`--write`
"""""""""""""""

Passing :code:`--write` will make *PyMend* write back to the files in place.

:code:`--check`
"""""""""""""""

Passing :code:`--check` will make *PyMend* exit with:

- code 0 if nothing would change;
- code 1 if some files had issues; or
- code 123 if there was an internal error

.. code:: console

    $ pymend test.py --check
    All done! ✨ 🍰 ✨
    1 file would be left unchanged.
    $ echo $?
    0

    $ pymend test.py --check
    would reformat test.py
    Oh no! 💥 💔 💥
    1 file would be reformatted, 1 file had issues.

    The following issues were found in file tests/test_pymend/refs/class_body.py:

    Module:
    Missing short description.

    A:
    Missing short description.
    Missing attribute `test1`.
    Missing attribute `test2`.
    Missing attribute `test3`.
    Missing attribute `test4`.
    Missing attribute `x`.
    Missing method `c(c)`.
    Missing method `d(pos, /, a: 'annotation', b: int, c: int, *args: list, d: int=5, e='test', **kwargs: dict)`.

    $ echo $?
    1

    $ pymend test.py --check
    error: cannot format test.py: INTERNAL ERROR: PyMend produced different docstrings on the second pass. Please report a bug on https://github.com/JanEricNitschke/pymend.  This diff might be helpful: /tmp/blk_kjdr1oog.log
    Oh no! 💥 💔 💥
    1 file would fail to reformat.
    $ echo $?
    123

This flag does not only look for missing or wrong information, it also flags
things that are left at their default *PyMend* values. This way you can have *PyMend*
fix your files in place but still warn you when you forgot to overwrite the placeholders
in the template with the actual information.


:code:`--force-params` / :code:`--unforce-params`
"""""""""""""""""""""""""""""""""""""""""""""""""

This option turns on/off the forcing of parameters to be named in the docstring.
If turned off then *PyMend* will only create a "Parameters" section if a function or
class had no docstring at all. It will also still fix the type information and add
a default description if that was missing. However it will not create a "Parameters"
section for existing docstrings and it will not add individual parameters that were
found in the signature but are missing in the existing docstring.

:code:`--force-params-min-n-params`
"""""""""""""""""""""""""""""""""""

This option gives you a bit more control over when you want to force a parameter section.
If :code:`--force-params` is enabled then this allows you some control for functions to
still not be forced to have parameter section. If the function has fewer parameters than
what is specified in this option then a parameters section is not forced.

Note that this does not count the "self" parameter for methods.

:code:`--force-defaults` / :code:`--unforce-defaults`
"""""""""""""""""""""""""""""""""""""""""""""""""""""

Whether to require parameter descriptions to state/explain their default values
if one was found in the signature.

:code:`--force-return` / :code:`--unforce-return`
"""""""""""""""""""""""""""""""""""""""""""""""""

The same as :code:`--force-params` but for the return section. If enabled then
a return section will always be created. If not, then one will only be created
if the docstring was missing entirely.

Regardless *PyMend* will always fix the type information and add a default description.
If *PyMend* detects multiple return descriptions together with multiple return values
in the body then it will add any missing returned values regardless of this setting.

:code:`--force-meta-min-func-length`
""""""""""""""""""""""""""""""""""""
This setting is similar to :code:`--force-params-min-n-params`. It allows you to
specify a minimum length for functions to be forced to have a "Parameters" or
"Returns" section. It applies to both sections. For "Parameters" sections it combines
with :code:`--force-params-min-n-params` by requiring that both conditions are met.

:code:`--force-raises` / :code:`--unforce-raises`
"""""""""""""""""""""""""""""""""""""""""""""""""

Force the docstring to have a "Raises" section if anything is being raised in the body.
Also add any missing raised exceptions that were found in the body but were missing in the docstring.

:code:`--force-methods` / :code:`--unforce-methods`
"""""""""""""""""""""""""""""""""""""""""""""""""""

Force class docstrings to have a method section with all methods that were
found in the body to be listed there. Excludes class and static methods as well
as properties (and setters and deleters).

:code:`--force-attributes` / :code:`--unforce-attributes`
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Force class docstrings to have an attribute section with all attributes that were
found to be defined in the :code:`__init__` method. Also includes properties.

:code:`--ignore-privates` / :code:`--handle-privates`
"""""""""""""""""""""""""""""""""""""""""""""""""""""

Toggle for whether to ignore attributes and methods that start with an underscore '_'.
his also means that methods with two underscores are ignored.
Consequently turning this off also forces processing of such methods.
Dunder methods are an exception and are always ignored regardless of this setting.

:code:`--ignore-unused-arguments` / :code:`--handle-unused-arguments`
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Toggle for whether to ignore arguments starting with an underscore '_'.

:code:`--ignored-decorators`
""""""""""""""""""""""""""""

Specify a list of decorators that should cause the function to be ignored
when processing docstrings. Current default is to ignore all function decorated
with :code:`@overload`.

:code:`--ignored-functions`
"""""""""""""""""""""""""""

Specify any functions to be ignored when processing docstrings. Ignore any
function that is an exact match to any of those specified here. One case where
this is useful is for CLI apps with `click <https://click.palletsprojects.com/en/8.1.x/>`__
where the arguments are passed to the annotated function. Here they would already
be documented via the click option and do not need further descriptions in the docstring.

:code:`--ignored-classes`
"""""""""""""""""""""""""

Specify any function by name that should be ignored when processing docstrings.
Only exact matches are ignored, these are not regexes.

:code:`--version`
"""""""""""""""""

You can check the version of *PyMend* you have installed using the :code:`--version` flag.

.. code:: console

    $ pymend --version
    pymend, 1.0.5


:code:`--config`
""""""""""""""""

Read configuration options from a configuration file. See
[below](#configuration-via-a-file) for more details on the configuration file.

:code:`-h`, :code:`--help`
""""""""""""""""""""""""""

Show available command-line options and exit.

Writeback and reporting
^^^^^^^^^^^^^^^^^^^^^^^

By default *PyMend* writes out patch files if there was anything that needed to change.
Sometimes you want *PyMend* to directly fix the files in place. For that there exists the flag:

-  :code:`--write` (exit with code 1 if any file would be reformatted)

Additionally you might want pymend to perform a more thorough check and report
all issues that it found. For that you can use:

-  :code:`--check` (exit with code 1 if any file has issues)

This flag does not only look for missing or wrong information, it also flags
things that are left at their default *PyMend* values. This way you can have *PyMend*
fix your files in place but still warn you when you forgot to overwrite the placeholders
in the template with the actual information.

Both variations can be enabled at once.

Output verbosity
^^^^^^^^^^^^^^^^

*PyMend* in general tries to produce the right amount of output,
balancing between usefulness and conciseness. By default, *PyMend* emits
files modified and error messages, plus a short summary.

.. code:: console

   $ pymend src/*.py
   error: cannot format src/pymend_primer/cli.py: Cannot parse: 5:6: port asyncio
   reformatted src/pymend_primer/lib.py
   reformatted src/pymendd/__init__.py
   reformatted src/pymend/__init__.py
   Oh no! 💥 💔 💥
   3 files reformatted, 2 files left unchanged, 1 file failed to reformat.

The :code:`--quiet` and :code:`--verbose` flags control output verbosity.

Configuration via a file
^^^^^^^^^^^^^^^^^^^^^^^^

*PyMend* is able to read project-specific default values for its command
line options from a :code:`pyproject.toml` file. This is especially useful
for specifying custom :code:`--exclude` / :code:`--extend-exclude` patterns for your
project.

**Pro-tip**: If you're asking yourself "Do I need to configure
anything?" the answer is "No". *PyMend* is all about sensible defaults.
Applying those defaults will have your code in compliance with many
other *PyMend* formatted projects.

What on Earth is a :code:`pyproject.toml` file?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`PEP 518 <https://www.python.org/dev/peps/pep-0518/>`__ defines
:code:`pyproject.toml` as a configuration file to store build system
requirements for Python projects. With the help of tools like
`Poetry <https://python-poetry.org/>`__,
`Flit <https://flit.readthedocs.io/en/latest/>`__, or
`Hatch <https://hatch.pypa.io/latest/>`__ it can fully replace the need
for :code:`setup.py` and :code:`setup.cfg` files.

Where *PyMend* looks for the file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default *PyMend* looks for :code:`pyproject.toml` starting from the common
base directory of all files and directories passed on the command line.
If it's not there, it looks in parent directories. It stops looking when
it finds the file, or a :code:`.git` directory, or a :code:`.hg` directory, or
the root of the file system, whichever comes first.

You can also explicitly specify the path to a particular file that you
want with :code:`--config`. In this situation *PyMend* will not look for any
other file.

If you're running with :code:`--verbose`, you will see a blue message if a
file was found and used.

Configuration format
^^^^^^^^^^^^^^^^^^^^

As the file extension suggests, :code:`pyproject.toml` is a
`TOML <https://github.com/toml-lang/toml>`__ file. It contains separate
sections for different tools. *PyMend* is using the :code:`[tool.pymend]`
section. The option keys are the same as long names of options on the
command line.

Note that you have to use single-quoted strings in TOML for regular
expressions. It's the equivalent of r-strings in Python. Multiline
strings are treated as verbose regular expressions by pymend. Use :code:`[ ]`
to denote a significant space character.

.. raw:: html

   <details>

.. raw:: html

   <summary>

Example pyproject.toml

.. raw:: html

   </summary>

.. code:: toml

   [tool.pymend]
    output-style      = "numpydoc"
    input-style       = "numpydoc"
    ignored-functions = ["main"]
    check             = true
   # 'extend-exclude' excludes files or directories in addition to the defaults
   extend-exclude = '''
   # A regex preceded with ^/ will apply only to files and directories
   # in the root of the project.
   (
     ^/foo.py    # exclude a file named foo.py in the root of the project
     | .*_pb2.py  # exclude autogenerated Protocol Buffer files anywhere in the project
   )
   '''

.. raw:: html

   </details>
