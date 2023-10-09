#!/usr/bin/python
"""Command line interface for pymend."""

import argparse

import pymend.docstring_parser as dsp
from pymend import PyComment

STRING_TO_STYLE = {
    "rest": dsp.DocstringStyle.REST,
    "javadoc": dsp.DocstringStyle.EPYDOC,
    "numpydoc": dsp.DocstringStyle.NUMPYDOC,
    "google": dsp.DocstringStyle.GOOGLE,
}


def run(
    files: list[str],
    *,
    overwrite: bool = False,
    output_style: dsp.DocstringStyle = dsp.DocstringStyle.NUMPYDOC,
) -> None:
    r"""Run pymend over the list of files..

    Parameters
    ----------
    files : list[str]
        List of files to analyze and fix.
    overwrite : bool
        Whether to overwrite the source file directly instead of creating
        a patch. (Default value = False)
    output_style : dsp.DocstringStyle
        Output style to use for the modified docstrings.
        (Default value = dsp.DocstringStyle.NUMPYDOC)

    Raises
    ------
    AssertionError
        If the input and output lines are identical but pyment reports
        some elements to have changed.
    """
    for file in files:
        comment = PyComment(
            file,
            output_style=output_style,
        )
        if overwrite:
            comment.output_fix()
        else:
            comment.output_patch()


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Generates patches after (re)writing docstrings."
    )
    parser.add_argument(
        "path",
        type=str,
        nargs="+",
        help="Python files to process."
        " If set to '-' lines are instead read from stdin.",
    )
    parser.add_argument(
        "-w",
        "--write",
        action="store_true",
        dest="overwrite",
        default=False,
        help="Don't write patches. Overwrite files instead. "
        "If used with path '-' won't overwrite but write "
        "to stdout the new content instead of a patch/.",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="style",
        default="numpydoc",
        help="Output docstring style in ['javadoc', 'rest', 'numpydoc', 'google']"
        " (default 'numpydoc')",
    )

    args = parser.parse_args()

    files = args.path
    run(
        files,
        overwrite=args.overwrite,
        output_style=STRING_TO_STYLE[args.output.lower()],
    )


if __name__ == "__main__":
    main()
