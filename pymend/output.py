"""Nice output for pymend.

The double calls are for patching purposes in tests.
"""

import difflib
import tempfile
from typing import Any, Optional

from click import echo, style


def out(
    message: Optional[str] = None, *, nl: bool = True, **styles: Any  # noqa: ANN401
) -> None:
    """Output normal message.

    Parameters
    ----------
    message : Optional[str]
        Message to output (Default value = None)
    nl : bool
        Whether to print a newline after the message. (Default value = True)
    **styles : Any
        Style options for click.
    """
    if message is not None:
        if "bold" not in styles:
            styles["bold"] = True
        message = style(message, **styles)
    echo(message, nl=nl, err=True)


def err(
    message: Optional[str] = None, *, nl: bool = True, **styles: Any  # noqa: ANN401
) -> None:
    """Output error message.

    Parameters
    ----------
    message : Optional[str]
        Message to output (Default value = None)
    nl : bool
        Whether to print a newline after the message. (Default value = True)
    **styles : Any
        Style options for click.
    """
    if message is not None:
        if "fg" not in styles:
            styles["fg"] = "red"
        message = style(message, **styles)
    echo(message, nl=nl, err=True)


def diff(a: list[str], b: list[str], a_name: str, b_name: str) -> list[str]:
    """Return a unified diff list between lists`a` and `b`.

    Parameters
    ----------
    src : list[str]
        Source for the diff
    dst : list[str]
        Target for the diff.
    source_path : str
        Path to the source file of the diff. (Default value = '')
    target_path : str
        Path to the target file of the diff. (Default value = '')

    Returns
    -------
    list[str]
        The resulting diff
    """
    diff_lines: list[str] = []
    for line in difflib.unified_diff(a, b, fromfile=a_name, tofile=b_name):
        # Work around https://bugs.python.org/issue2142
        # See:
        # https://www.gnu.org/software/diffutils/manual/html_node/Incomplete-Lines.html
        if line[-1] == "\n":
            diff_lines.append(line)
        else:
            diff_lines.append(line + "\n")
            diff_lines.append("\\ No newline at end of file\n")
    return diff_lines


def color_diff(contents: str) -> str:
    """Inject the ANSI color codes to the diff.

    Parameters
    ----------
    contents : str
        Diff content to color.

    Returns
    -------
    str
        Colored diff.
    """
    lines = contents.split("\n")
    for i, line in enumerate(lines):
        if line.startswith(("+++", "---")):
            line = "\033[1m" + line + "\033[0m"  # bold, reset  # noqa: PLW2901
        elif line.startswith("@@"):
            line = "\033[36m" + line + "\033[0m"  # cyan, reset  # noqa: PLW2901
        elif line.startswith("+"):
            line = "\033[32m" + line + "\033[0m"  # green, reset # noqa: PLW2901
        elif line.startswith("-"):
            line = "\033[31m" + line + "\033[0m"  # red, reset # noqa: PLW2901
        lines[i] = line
    return "\n".join(lines)


def dump_to_file(*output: str, ensure_final_newline: bool = True) -> str:
    """Dump `output` to a temporary file. Return path to the file.

    Parameters
    ----------
    *output : str
        List of strings to dump into the output.
    ensure_final_newline : bool
        Whether to make sure that every dumped string
        ends in a new line. (Default value = True)

    Returns
    -------
    str
        Path to the produced temp file.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", prefix="blk_", suffix=".log", delete=False, encoding="utf8"
    ) as f:
        for lines in output:
            f.write(lines)
            if ensure_final_newline and lines and lines[-1] != "\n":
                f.write("\n")
    return f.name
