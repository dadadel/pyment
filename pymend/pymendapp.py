#!/usr/bin/python
"""Command line interface for pymend."""

import re
import traceback
from re import Pattern
from typing import Any, Optional, Union

import click

import pymend.docstring_parser as dsp
from pymend import PyComment

from .const import DEFAULT_EXCLUDES
from .files import find_pyproject_toml, parse_pyproject_toml
from .output import out
from .report import Report

STRING_TO_STYLE = {
    "rest": dsp.DocstringStyle.REST,
    "javadoc": dsp.DocstringStyle.EPYDOC,
    "numpydoc": dsp.DocstringStyle.NUMPYDOC,
    "google": dsp.DocstringStyle.GOOGLE,
}


def path_is_excluded(
    normalized_path: str,
    pattern: Optional[Pattern[str]],
) -> bool:
    """Check if a path is excluded because it matches and exclusion regex.

    Parameters
    ----------
    normalized_path : str
        Normalized path to check
    pattern : Optional[Pattern[str]]
        Optionally a regex pattern to check against

    Returns
    -------
    bool
        True if the path is excluded by the regex.
    """
    match = pattern.search(normalized_path) if pattern else None
    return bool(match and match.group(0))


def output_stye_option_callback(
    _c: click.Context, _p: Union[click.Option, click.Parameter], style: str
) -> dsp.DocstringStyle:
    """Compute the output style from a --output_stye flag.

    Parameters
    ----------
    style : str
        String representation of the style to use.

    Returns
    -------
    dsp.DocstringStyle
        Style to use.
    """
    return STRING_TO_STYLE[style]


def re_compile_maybe_verbose(regex: str) -> Pattern[str]:
    """Compile a regular expression string in `regex`.

    If it contains newlines, use verbose mode.

    Parameters
    ----------
    regex : str
        _description_

    Returns
    -------
    Pattern[str]
        _description_
    """
    if "\n" in regex:
        regex = "(?x)" + regex
    compiled: Pattern[str] = re.compile(regex)
    return compiled


def validate_regex(
    _ctx: click.Context,
    _param: click.Parameter,
    value: Optional[str],
) -> Optional[Pattern[str]]:
    """Validate the regex from command line.

    Parameters
    ----------
    value : Optional[str]
        Regex pattern to validate.

    Returns
    -------
    Optional[Pattern[str]]
        Compiled regex pattern or None if the input was None.

    Raises
    ------
    click.BadParameter
        If the value is not a valid regex.
    """
    try:
        return re_compile_maybe_verbose(value) if value is not None else None
    except re.error as e:
        msg = f"Not a valid regular expression: {e}"
        raise click.BadParameter(msg) from None


def run(
    files: tuple[str, ...],
    *,
    overwrite: bool = False,
    output_style: dsp.DocstringStyle = dsp.DocstringStyle.NUMPYDOC,
    exclude: Optional[Pattern[str]],
    extend_exclude: Optional[Pattern[str]],
    report: Report,
) -> None:
    r"""Run pymend over the list of files..

    Parameters
    ----------
    files : tuple[str, ...]
        List of files to analyze and fix.
    overwrite : bool
        Whether to overwrite the source file directly instead of creating
        a patch. (Default value = False)
    output_style : dsp.DocstringStyle
        Output style to use for the modified docstrings.
        (Default value = dsp.DocstringStyle.NUMPYDOC)
    exclude : Optional[Pattern[str]]
        Optional regex pattern to use to exclude files from reformatting.
    extend_exclude : Optional[Pattern[str]]
        Additional regexes to add onto the exclude pattern.
        Useful if one just wants to add some to the existing default.
    report : Report
        Reporter for pretty communication with the user.

    Raises
    ------
    AssertionError
        If the input and output lines are identical but pyment reports
        some elements to have changed.
    """
    for file in files:
        if path_is_excluded(file, exclude):
            report.path_ignored(file, "matches the --exclude regular expression")
            continue
        if path_is_excluded(file, extend_exclude):
            report.path_ignored(file, "matches the --extend-exclude regular expression")
            continue
        try:
            comment = PyComment(
                file,
                output_style=output_style,
            )
            # Not using ternary when the calls have side effects
            if overwrite:  # noqa: SIM108
                changed = comment.output_fix()
            else:
                changed = comment.output_patch()
            report.done(file, changed)
        except Exception as exc:  # noqa: BLE001
            if report.verbose:
                traceback.print_exc()
            report.failed(file, str(exc))


def read_pyproject_toml(
    ctx: click.Context, _param: click.Parameter, value: Optional[str]
) -> Optional[str]:
    """Inject Black configuration from "pyproject.toml" into defaults in `ctx`.

    Returns the path to a successfully found and read configuration file, None
    otherwise.

    Parameters
    ----------
    ctx : click.Context
        Context containing preexisting default values.
    value : Optional[str]
        Optionally path to the config file.

    Returns
    -------
    Optional[str]
        Path to the config file if one was found or specified.

    Raises
    ------
    click.FileError
        If there was a problem reading the configuration file.
    click.BadOptionUsage
        If the value passed for `exclude` was not a string.
    click.BadOptionUsage
        If the value passed for `extended_exclude` was not a string.
    """
    if not value:
        value = find_pyproject_toml(ctx.params.get("src", ()))
        if value is None:
            return None

    try:
        config = parse_pyproject_toml(value)
    except (OSError, ValueError) as e:
        raise click.FileError(
            filename=value, hint=f"Error reading configuration file: {e}"
        ) from None

    if not config:
        return None
    # Sanitize the values to be Click friendly. For more information please see:
    # https://github.com/psf/black/issues/1458
    # https://github.com/pallets/click/issues/1567
    config: dict[str, Any] = {
        k: str(v) if not isinstance(v, (list, dict)) else v for k, v in config.items()
    }

    exclude = config.get("exclude")
    if exclude is not None and not isinstance(exclude, str):
        raise click.BadOptionUsage("exclude", "Config key exclude must be a string")

    extend_exclude = config.get("extend_exclude")
    if extend_exclude is not None and not isinstance(extend_exclude, str):
        raise click.BadOptionUsage(
            "extend-exclude", "Config key extend-exclude must be a string"
        )

    default_map: dict[str, Any] = {}
    if ctx.default_map:
        default_map.update(ctx.default_map)
    default_map.update(config)

    ctx.default_map = default_map
    return value


@click.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    # While Click does set this field automatically using the docstring, mypyc
    # (annoyingly) strips 'em so we need to set it here too.
    help="Create, update or convert docstrings.",
)
@click.option(
    "-o",
    "--output-style",
    type=click.Choice(list(STRING_TO_STYLE)),
    callback=output_stye_option_callback,
    multiple=False,
    default="numpydoc",
    help=(
        "Output docstring style in ['javadoc', 'rest', 'numpydoc', 'google']"
        " (default 'numpydoc')"
    ),
)
@click.option(
    "--check",
    is_flag=True,
    help=(
        "Perform check if file is properly docstringed."
        " Can be used alongside --write and also reports negatively on pymend defaults."
        " Return code 0 means"
        " nothing would change. Return code 1 means some files would be reformatted."
        " Return code 123 means there was an internal error."
    ),
)
@click.option(
    "--write/--diff",
    is_flag=True,
    default=False,
    help="Directly overwrite the source files instead of just producing a patch.",
)
@click.option(
    "--exclude",
    type=str,
    callback=validate_regex,
    help=(
        "A regular expression that matches files and directories that should be"
        " excluded. An empty value means no paths are excluded."
        " Use forward slashes for directories on all platforms (Windows, too)."
        f"[default: {DEFAULT_EXCLUDES}]"
    ),
    show_default=False,
)
@click.option(
    "--extend-exclude",
    type=str,
    callback=validate_regex,
    help=(
        "Like --exclude, but adds additional files and directories on top of the"
        " excluded ones. (Useful if you simply want to add to the default)"
    ),
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help=(
        "Don't emit non-error messages to stderr. Errors are still emitted; silence"
        " those with 2>/dev/null."
    ),
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help=(
        "Also emit messages to stderr about files that were not changed or were ignored"
        " due to exclusion patterns."
    ),
)
@click.argument(
    "src",
    nargs=-1,
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True, allow_dash=True
    ),
    required=True,
    is_eager=True,
    metavar="SRC ...",
)
@click.option(
    "--config",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        allow_dash=False,
        path_type=str,
    ),
    is_eager=True,
    callback=read_pyproject_toml,
    help="Read configuration from FILE path.",
)
@click.pass_context
def main(  # pylint: disable=too-many-arguments
    ctx: click.Context,
    *,
    write: bool,
    output_style: dsp.DocstringStyle,
    check: bool,
    quiet: bool,
    verbose: bool,
    exclude: Optional[Pattern[str]],
    extend_exclude: Optional[Pattern[str]],
    src: tuple[str, ...],
    config: Optional[str],
) -> None:
    """Create, update or convert docstrings.

    Parameters
    ----------
    ctx : click.Context
        Currently only used to exit the application.
    write : bool
        Whether to overwrite files directly
    output_style : dsp.DocstringStyle
        Which output style to use.
    check : bool
        CURRENTLY DOES NOTHING! TODO!
        Whether to perform a check if all docstrings are properly formatted.
        Works alongside --write and is stricter than it as it considers
        pymend default values as not properly formatted.
    quiet : bool
        Silence output as much as possible.
    verbose : bool
        Increase output to include a lot more information.
    exclude : Optional[Pattern[str]]
        Optional regex pattern to use to exclude files from reformatting.
    extend_exclude : Optional[Pattern[str]]
        Additional regexes to add onto the exclude pattern.
        Useful if one just wants to add some to the existing default.
    src : tuple[str, ...]
        Source files to fix.
    config : Optional[str]
        Path to config file to use. If None is provided a pyproject.toml
        file is looked for in the source files common parents paths.
    """
    ctx.ensure_object(dict)
    # Temp to turn off unused variable warnings.
    if f"{check, config}":
        pass
    report = Report(check=check, diff=not write, quiet=quiet, verbose=verbose)
    run(
        src,
        overwrite=write,
        output_style=output_style,
        exclude=exclude,
        extend_exclude=extend_exclude,
        report=report,
    )
    if verbose or not quiet:
        if verbose or report.change_count or report.failure_count:
            out()
        error_msg = "Oh no! 💥 💔 💥"
        out(error_msg if report.return_code else "All done! ✨ 🍰 ✨")
        click.echo(str(report), err=True)
    ctx.exit(report.return_code)
