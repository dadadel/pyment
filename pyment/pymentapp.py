#!/usr/bin/python
"""Command line interface for pyment."""

import argparse
import os
import sys
from typing import List, Optional

from pyment import PyComment

# The maximum depth to reach while recursively exploring sub folders
MAX_DEPTH_RECUR = 50


def run(  # pylint: disable=too-many-locals, too-many-branches
    source: str,
    files: Optional[List[str]] = None,
    *,
    overwrite: bool = False,
) -> None:
    r"""_summary_.

    Parameters
    ----------
    source : str
        _description_
    files : Optional[List[str]]
        _description_ (Default value = [])
    config_file : Optional[str]
        _description_ (Default value = None)
    overwrite : bool
        _description_ (Default value = False)
    """
    if files is None:
        files = []

    for file in files:
        if os.path.isdir(source):
            path = (
                source
                + os.sep
                + os.path.relpath(os.path.abspath(file), os.path.abspath(source))
            )
            path = path[: -len(os.path.basename(file))]
        else:
            path = ""

        comment = PyComment(
            file,
        )
        comment.proceed()

        list_from: List[str] = []
        lines_to_write: List[str] = []
        list_changed: List[str] = []
        if overwrite:
            list_from, lines_to_write, list_changed = comment.compute_before_after()
            if (list_from == lines_to_write) != (len(list_changed) == 0):
                msg = (
                    f"The file {file} having changed should be identical "
                    "to any function having changed! "
                    f"However the list of changed functions was {list_changed}"
                    " but the difference between the files "
                    f"was {list(set(list_from) ^ set(lines_to_write))}!"
                )
                raise AssertionError(msg)
            if list_from != lines_to_write:
                print(
                    "Modified docstrings of element"
                    f'{"s" if len(list_changed) > 1 else ""} '
                    f'({", ".join(list_changed)}) in file {file}.'
                )
                comment.overwrite_source_file(lines_to_write)
        else:
            lines_to_write = comment.get_patch_lines(path, path)

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
        help="python files or folders containing python files to "
        "proceed (explore also sub-folders)."
        " Use '-' to read from stdin and write to stdout",
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

    args = parser.parse_args()
    source = ""

    files = args.path
    if not files:
        msg = BaseException(f"No files were found matching {args.path}")
        raise msg

    run(
        source,
        files,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
