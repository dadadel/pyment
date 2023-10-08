#!/usr/bin/python
"""Command line interface for pymend."""

import argparse
import os
import sys

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
        comment.proceed()

        list_from: list[str] = []
        lines_to_write: list[str] = []
        list_changed: list[str] = []
        if overwrite:
            list_from, lines_to_write, list_changed = comment.compute_before_after()
            if (list_from == lines_to_write) != (len(list_changed) == 0):
                log = comment.dump_to_file(
                    "INTERNAL ERROR: "
                    "Pymend reported some elements to have changed "
                    "but the output is identical to the input.\n",
                    "List of changed elements:\n",
                    "\n".join(list_changed),
                    "Original file\n",
                    "".join(list_from),
                )
                msg = (
                    "INTERNAL ERROR: "
                    "Pymend reported some elements to have changed "
                    "but the output is identical to the input. "
                    " Please report a bug on"
                    " https://github.com/JanEricNitschke/pymend/issues."
                    f" This invalid output might be helpful: {log}"
                )
                raise AssertionError(msg)
            if file == "-":
                sys.stdout.writelines(lines_to_write)
            elif list_from != lines_to_write:
                print(
                    "Modified docstrings of element"
                    f'{"s" if len(list_changed) > 1 else ""} '
                    f'({", ".join(list_changed)}) in file {file}.'
                )
                comment.overwrite_source_file(lines_to_write)
        else:
            lines_to_write = comment.get_patch_lines(file, file)

            if file == "-":
                sys.stdout.writelines(lines_to_write)
            else:
                comment.write_patch_file(
                    f"{os.path.basename(file)}.patch", lines_to_write
                )


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
