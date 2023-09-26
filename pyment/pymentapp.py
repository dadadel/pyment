#!/usr/bin/python
"""Command line interface for pyment."""

import argparse
import glob
import os
import sys
from typing import Dict, List, Optional

from pyment import PyComment, __author__, __copyright__, __licence__, __version__

# The maximum depth to reach while recursively exploring sub folders
MAX_DEPTH_RECUR = 50


def tobool(test_string: str) -> bool:
    """Turn string into bool.

    Parameters
    ----------
    test_string :str
        String to convert

    Returns
    -------
    bool
        Whether the string represented 'true'
    """
    return test_string.lower() == "true"


def get_files_from_dir(
    path: str, *, recursive: bool = True, depth: int = 0, file_ext: str = ".py"
) -> List[str]:
    """Retrieve the list of files from a folder.

    Parameters
    ----------
    path : str
        file or directory where to search files
    recursive : bool
        Ff True will search also sub-directories (Default value = True)
    depth : int
        If set, explore recursively.
        The depth of sub directories to follow (Default value = 0)
    file_ext : str
        The files extension to get. (Default value = '.py'')

    Returns
    -------
    List[str]
        the file list retrieved. if the input is a file then a one element list.
    """
    file_list = []
    if os.path.isfile(path) or path == "-":
        return [path]
    if path[-1] != os.sep:
        path += os.sep
    for file in glob.glob(f"{path}*"):
        if os.path.isdir(file):
            if depth < MAX_DEPTH_RECUR:  # avoid infinite recursive loop
                file_list.extend(
                    get_files_from_dir(file, recursive=recursive, depth=depth + 1)
                )
            else:
                continue
        elif file.endswith(file_ext):
            file_list.append(file)
    return file_list


def get_config(config_file: Optional[str]) -> Dict:
    """Get the configuration from a file.

    Parameters
    ----------
    config_file : str
        the configuration file

    Returns
    -------
    dict
        the configuration
    """
    config = {}

    if config_file:
        try:
            with open(config_file, encoding="utf-8") as file:
                lines = file.readlines()
        except Exception:  # noqa: BLE001 pylint: disable=broad-exception-caught
            print(f"Unable to open configuration file '{config_file}'")
        else:
            for line in lines:
                if len(line.strip()):
                    key, value = line.split("=", 1)
                    key, value = key.strip(), value.strip()
                    if key in ["init2class", "first_line", "convert_only"]:
                        value = tobool(value)
                    if key == "indent":
                        value = int(value)
                    config[key] = value
    return config


def run(  # noqa: PLR0913, PLR0912 pylint: disable=too-many-locals, too-many-branches
    source: str,
    files: Optional[List[str]] = None,
    input_style: Optional[str] = "auto",
    output_style: str = "numpydoc",
    *,
    first_line: bool = True,
    quotes: str = '"""',
    init2class: bool = False,
    convert: bool = False,
    config_file: Optional[str] = None,
    ignore_private: bool = False,
    overwrite: bool = False,
) -> None:
    r"""_summary_.

    Parameters
    ----------
    source : str
        _description_
    files : Optional[List[str]]
        _description_ (Default value = [])
    input_style : Optional[str]
        _description_ (Default value = 'auto')
    output_style : str
        _description_ (Default value = 'reST')
    first_line : bool
        _description_ (Default value = True)
    quotes : str
        _description_ (Default value = '\"\"\"')
    init2class : bool
        _description_ (Default value = False)
    convert : bool
        _description_ (Default value = False)
    config_file : Optional[str]
        _description_ (Default value = None)
    ignore_private : bool
        _description_ (Default value = False)
    overwrite : bool
        _description_ (Default value = False)
    """
    if files is None:
        files = []
    if input_style == "auto":
        input_style = None

    config = get_config(config_file)
    if "init2class" in config:
        init2class = config.pop("init2class")
    if "convert_only" in config:
        convert = config.pop("convert_only")
    if "quotes" in config:
        quotes = config.pop("quotes")
    if "input_style" in config:
        input_style = config.pop("input_style")
    if "output_style" in config:
        output_style = config.pop("output_style")
    if "first_line" in config:
        first_line = config.pop("first_line")
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
            quotes=quotes,
            input_style=input_style,
            output_style=output_style,
            first_line=first_line,
            ignore_private=ignore_private,
            convert_only=convert,
            **config,
        )
        comment.proceed()
        if init2class:
            comment.docs_init_to_class()

        list_from: List[str] = []
        list_to: List[str] = []
        list_changed: List[str] = []
        if overwrite:
            list_from, list_to, list_changed = comment.compute_before_after()
            if (list_from == list_to) != (len(list_changed) == 0):
                msg = (
                    f"The file {file} having changed should be identical "
                    "to any function having changed! "
                    f"However the list of changed functions was {list_changed}"
                    " but the difference between the files "
                    f"was {list(set(list_from) ^ set(list_to))}!"
                )
                raise AssertionError(msg)
            lines_to_write = list_to
        else:
            lines_to_write = comment.get_patch_lines(path, path)

        if file == "-":
            sys.stdout.writelines(lines_to_write)
        elif overwrite:
            if list_from != list_to:
                print(
                    "Modified docstrings of element"
                    f'{"s" if len(list_changed) > 1 else ""} '
                    f'({", ".join(list_changed)}) in file {file}.'
                )
                comment.overwrite_source_file(lines_to_write)
        else:
            comment.write_patch_file(f"{os.path.basename(file)}.patch", lines_to_write)


def main() -> None:
    """Entry point."""
    desc = f"Pyment v{__version__} - {__copyright__} - {__author__} - {__licence__}"
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
        "-i",
        "--input",
        metavar="style",
        default="auto",
        dest="input",
        help="Input docstring style in "
        "['javadoc', 'reST', 'numpydoc', 'google', 'auto']"
        " (default autodetected)",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="style",
        default="numpydoc",
        dest="output",
        help="Output docstring style in "
        "['javadoc', 'reST', 'numpydoc', 'google'] "
        "(default 'numpydoc')",
    )
    parser.add_argument(
        "-q",
        "--quotes",
        metavar="quotes",
        default='"""',
        dest="quotes",
        help='Type of docstring delimiter quotes: \'\'\' or """ (default """). '
        "Note that you may escape the characters using \\ like \\'\\'\\', "
        "or surround it with the opposite quotes like \"'''\"",
    )
    parser.add_argument(
        "-f",
        "--first-line",
        metavar="status",
        default="True",
        dest="first_line",
        help="Does the comment starts on the first line after the quotes "
        "(default 'True')",
    )
    parser.add_argument(
        "-t",
        "--convert",
        action="store_true",
        default=False,
        help="Existing docstrings will be converted but won't create missing ones",
    )
    parser.add_argument(
        "-c",
        "--config-file",
        metavar="config",
        default="",
        dest="config_file",
        help="Get a Pyment configuration from a file. "
        "Note that the config values will overload the command line ones.",
    )
    parser.add_argument(
        "-d",
        "--init2class",
        help="If no docstring to class, then move the __init__ one",
        action="store_true",
    )
    parser.add_argument(
        "-p",
        "--ignore-private",
        metavar="status",
        default="False",
        dest="ignore_private",
        help="Don't process the private methods/functions "
        "starting with __ (two underscores) (default 'True')",
    )
    parser.add_argument("-v", "--version", action="version", version=desc)
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
    config_file = args.config_file or ""


    run(
        source,
        files,
        args.input,
        args.output,
        first_line=tobool(args.first_line),
        quotes=args.quotes,
        init2class=args.init2class,
        convert=args.convert,
        config_file=config_file,
        ignore_private=tobool(args.ignore_private),
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
