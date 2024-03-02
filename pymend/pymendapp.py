#!/usr/bin/python
"""Command line interface for pymend."""

import platform
import re
import traceback
from re import Pattern
from typing import Any, Optional, Union

import click
from click.core import ParameterSource

import pymend.docstring_parser as dsp
from pymend import PyComment, __version__

from .const import DEFAULT_EXCLUDES
from .files import find_pyproject_toml, parse_pyproject_toml
from .output import out
from .report import Report
from .types import FixerSettings

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


def style_option_callback(
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
    if style in STRING_TO_STYLE:
        return STRING_TO_STYLE[style]
    return dsp.DocstringStyle.AUTO


def re_compile_maybe_verbose(regex: str) -> Pattern[str]:
    """Compile a regular expression string in `regex`.

    If it contains newlines, use verbose mode.

    Parameters
    ----------
    regex : str
        Regex to compile.

    Returns
    -------
    Pattern[str]
        Compiled regex.
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
    input_style: dsp.DocstringStyle = dsp.DocstringStyle.AUTO,
    exclude: Pattern[str],
    extend_exclude: Optional[Pattern[str]],
    report: Report,
    fixer_settings: FixerSettings,
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
    input_style : dsp.DocstringStyle
        Input docstring style.
        Auto means that the style is detected automatically. Can cause issues when
        styles are mixed in examples or descriptions."
        (Default value = dsp.DocstringStyle.AUTO)
    exclude : Pattern[str]
        Optional regex pattern to use to exclude files from reformatting.
    extend_exclude : Optional[Pattern[str]]
        Additional regexes to add onto the exclude pattern.
        Useful if one just wants to add some to the existing default.
    report : Report
        Reporter for pretty communication with the user.
    fixer_settings : FixerSettings
        Settings for which fixes should be performed.

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
                input_style=input_style,
                fixer_settings=fixer_settings,
            )
            n_issues, issue_report = comment.report_issues()
            # Not using ternary when the calls have side effects
            if overwrite:  # noqa: SIM108
                changed = comment.output_fix()
            else:
                changed = comment.output_patch()
            report.done(
                file, changed=changed, issues=bool(n_issues), issue_report=issue_report
            )
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
        raise click.BadOptionUsage(
            "exclude",  # noqa: EM101
            "Config key exclude must be a string",
        )

    extend_exclude = config.get("extend_exclude")
    if extend_exclude is not None and not isinstance(extend_exclude, str):
        raise click.BadOptionUsage(
            "extend-exclude",  # noqa: EM101
            "Config key extend-exclude must be a string",
        )

    default_map: dict[str, Any] = {}
    if ctx.default_map:
        default_map.update(ctx.default_map)
    default_map.update(config)

    ctx.default_map = default_map
    return value


@click.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Create, update or convert docstrings.",
)
@click.option(
    "--write/--diff",
    is_flag=True,
    default=False,
    help="Directly overwrite the source files instead of just producing a patch.",
)
@click.option(
    "-o",
    "--output-style",
    type=click.Choice(list(STRING_TO_STYLE)),
    callback=style_option_callback,
    multiple=False,
    default="numpydoc",
    help=("Output docstring style."),
)
@click.option(
    "-i",
    "--input-style",
    type=click.Choice([*list(STRING_TO_STYLE), "auto"]),
    callback=style_option_callback,
    multiple=False,
    default="auto",
    help=(
        "Input docstring style."
        " Auto means that the style is detected automatically. Can cause issues when"
        " styles are mixed in examples or descriptions."
    ),
)
@click.option(
    "--check",
    is_flag=True,
    help=(
        "Perform check if file is properly docstringed."
        " Also reports negatively on pymend defaults."
        " Return code 0 means everything was perfect."
        " Return code 1 means some files would has issues."
        " Return code 123 means there was an internal error."
    ),
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
    "--force-params/--unforce-params",
    type=bool,
    is_flag=True,
    default=True,
    help="Whether to force a parameter section even if"
    " there is already an existing docstring. "
    "If set will also fill force the parameters section to name every parameter.",
)
@click.option(
    "--force-params-min-n-params",
    type=int,
    default=0,
    help="Minimum number of arguments detected in the signature "
    "to actually enforce parameters."
    " If less than the specified numbers of arguments are"
    " detected then a parameters section is only build for new docstrings."
    " No new sections are created for existing docstrings and existing sections"
    " are not extended. Only has an effect with --force-params set to true.",
)
@click.option(
    "--force-meta-min-func-length",
    type=int,
    default=0,
    help="Minimum number statements in the function body "
    "to actually enforce parameters."
    " If less than the specified numbers of arguments are"
    " detected then a parameters section is only build for new docstrings."
    " No new sections are created for existing docstrings and existing sections"
    " are not extended. Only has an effect with"
    " `--force-params` or `--force-return` set to true.",
)
@click.option(
    "--force-return/--unforce-return",
    type=bool,
    is_flag=True,
    default=True,
    help="Whether to force a return/yield section even if"
    " there is already an existing docstring. "
    "Will only actually force return/yield sections"
    " if any value return or yield is found in the body.",
)
@click.option(
    "--force-raises/--unforce-raises",
    type=bool,
    is_flag=True,
    default=True,
    help="Whether to force a raises section even if"
    " there is already an existing docstring."
    " Will only actually force the section if any raises were detected in the body."
    " However, if set it will force on entry in the section per raise detected.",
)
@click.option(
    "--force-methods/--unforce-methods",
    type=bool,
    is_flag=True,
    default=False,
    help="Whether to force a methods section for classes even if"
    " there is already an existing docstring."
    " If set it will force on entry in the section per method found."
    " If only some methods are desired to be specified then this should be left off.",
)
@click.option(
    "--force-attributes/--unforce-attributes",
    type=bool,
    is_flag=True,
    default=False,
    help="Whether to force an attributes section for classes even if"
    " there is already an existing docstring."
    " If set it will force on entry in the section per attribute found."
    " If only some attributes are desired then this should be left off.",
)
@click.option(
    "--ignore-privates/--handle-privates",
    is_flag=True,
    default=True,
    help="Whether to ignore attributes and methods that start with an underscore '_'."
    " This also means that methods with two underscores are ignored."
    " Consequently turning this off also forces processing of such methods."
    " Dunder methods are an exception and are"
    " always ignored regardless of this setting.",
)
@click.option(
    "--ignore-unused-arguments/--handle-unused-arguments",
    is_flag=True,
    default=True,
    help="Whether to ignore arguments starting with an underscore '_'"
    " are ignored when building parameter sections.",
)
@click.option(
    "--ignored-decorators",
    multiple=True,
    default=["overload"],
    help="Decorators that, if present,"
    " should cause a function to be ignored for docstring analysis and generation.",
)
@click.option(
    "--ignored-functions",
    multiple=True,
    default=["main"],
    help="Functions that should be ignored for docstring analysis and generation."
    " Only exact matches are ignored. This is not a regex pattern.",
)
@click.option(
    "--ignored-classes",
    multiple=True,
    default=[],
    help="Classes that should be ignored for docstring analysis and generation."
    " Only exact matches are ignored. This is not a regex pattern.",
)
@click.option(
    "--force-defaults/--unforce-defaults",
    is_flag=True,
    default=True,
    help="Whether to enforce descriptions need to"
    " name/explain the default value of their parameter.",
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
@click.version_option(
    version=__version__,
    message=(
        f"%(prog)s, %(version)s\n"
        f"Python ({platform.python_implementation()}) {platform.python_version()}"
    ),
)
@click.argument(
    "src",
    nargs=-1,
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True, allow_dash=False
    ),
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
def main(  # pylint: disable=too-many-arguments, too-many-locals  # noqa: PLR0913
    ctx: click.Context,
    *,
    write: bool,
    output_style: dsp.DocstringStyle,
    input_style: dsp.DocstringStyle,
    check: bool,
    exclude: Optional[Pattern[str]],
    extend_exclude: Optional[Pattern[str]],
    force_params: bool,
    force_params_min_n_params: bool,
    force_meta_min_func_length: bool,
    force_return: bool,
    force_raises: bool,
    force_methods: bool,
    force_attributes: bool,
    ignore_privates: bool,
    ignore_unused_arguments: bool,
    ignored_decorators: list[str],
    ignored_functions: list[str],
    ignored_classes: list[str],
    force_defaults: bool,
    quiet: bool,
    verbose: bool,
    src: tuple[str, ...],
    config: Optional[str],
) -> None:
    """Create, update or convert docstrings."""
    ctx.ensure_object(dict)

    if not src:
        out(main.get_usage(ctx) + "\n\nError: Missing argument 'SRC ...'.")
        ctx.exit(1)

    if verbose and config:
        config_source = ctx.get_parameter_source("config")
        if config_source in (
            ParameterSource.DEFAULT,
            ParameterSource.DEFAULT_MAP,
        ):
            out("Using configuration from project root.", fg="blue")
        else:
            out(f"Using configuration in '{config}'.", fg="blue")
        if ctx.default_map:
            for param, value in ctx.default_map.items():
                out(f"{param}: {value}")

    report = Report(check=check, diff=not write, quiet=quiet, verbose=verbose)
    fixer_settings = FixerSettings(
        force_params=force_params,
        force_return=force_return,
        force_raises=force_raises,
        force_methods=force_methods,
        force_attributes=force_attributes,
        force_params_min_n_params=force_params_min_n_params,
        force_meta_min_func_length=force_meta_min_func_length,
        ignore_privates=ignore_privates,
        ignore_unused_arguments=ignore_unused_arguments,
        ignored_decorators=ignored_decorators,
        ignored_functions=ignored_functions,
        ignored_classes=ignored_classes,
        force_defaults=force_defaults,
    )

    run(
        src,
        overwrite=write,
        output_style=output_style,
        input_style=input_style,
        exclude=exclude or DEFAULT_EXCLUDES,
        extend_exclude=extend_exclude,
        report=report,
        fixer_settings=fixer_settings,
    )

    if verbose or not quiet:
        if verbose or report.change_count or report.failure_count:
            out()
        error_msg = "Oh no! 💥 💔 💥"
        out(error_msg if report.return_code else "All done! ✨ 🍰 ✨")
        click.echo(str(report), err=True)
    ctx.exit(report.return_code)
