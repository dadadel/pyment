The configuration parameters that you can set in the configuration file are:

- first_line:

`True or False`

Set to **True** then for each docstring, the description should start on the first
line, just after the quotes. In the other case the description will start on the
second line.

- quotes:

`''' or """`

The quotes used for the docstring limits.

- output_style:

`javadoc, reST, numpydoc, groups`

The output format for the docstring.

- input_style:

`auto, javadoc, reST, numpydoc, groups`

The input format for the docstring interpretation. Set to **auto** if you want
Pyment to autodetect for each docstring its format.

- init2class:

`True or False`

Set to **True** to move the generated docstring for __init__ to the class docstring.
If there was already a docstring for the class, then the __init__ will conserve
its docstring and the class its own.
