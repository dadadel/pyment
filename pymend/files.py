"""File handling for pymend."""

import sys
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if sys.version_info >= (3, 11):
    try:
        import tomllib
    except ImportError:
        # Help users on older alphas
        if not TYPE_CHECKING:
            import tomli as tomllib
        else:
            raise
else:
    import tomli as tomllib


@lru_cache
def find_project_root(srcs: Sequence[str]) -> tuple[Path, str]:
    """Return a directory containing .git, .hg, or pyproject.toml.

    That directory will be a common parent of all files and directories
    passed in `srcs`.

    If no directory in the tree contains a marker that would specify it's the
    project root, the root of the file system is returned.

    Returns a two-tuple with the first element as the project root path and
    the second element as a string describing the method by which the
    project root was discovered.

    Parameters
    ----------
    srcs : Sequence[str]
        Source files that will be considered by pymend.

    Returns
    -------
    directory : Path
        Projects root path
    method : str
        Method by which the root path was determined.
    """
    if not srcs:
        srcs = [str(Path.cwd().resolve())]

    path_srcs = [Path(Path.cwd(), src).resolve() for src in srcs]

    # A list of lists of parents for each 'src'. 'src' is included as a
    # "parent" of itself if it is a directory
    src_parents = [
        list(path.parents) + ([path] if path.is_dir() else []) for path in path_srcs
    ]

    intersection: set[Path] = set[Path].intersection(
        *(set(parents) for parents in src_parents)
    )

    common_base = max(
        intersection,
        key=lambda path: path.parts,
    )

    # Directory will always be set in the loop.
    # This is just for pylint.
    directory = Path("")
    for directory in (common_base, *common_base.parents):
        if (directory / ".git").exists():
            return directory, ".git directory"

        if (directory / ".hg").is_dir():
            return directory, ".hg directory"

        if (directory / "pyproject.toml").is_file():
            return directory, "pyproject.toml"

    return directory, "file system root"


def find_pyproject_toml(path_search_start: tuple[str, ...]) -> Optional[str]:
    """Find the absolute filepath to a pyproject.toml if it exists.

    Parameters
    ----------
    path_search_start : tuple[str, ...]
        Tuple of paths to consider in the search for pyproject.toml

    Returns
    -------
    Optional[str]
        Path to pypyproject.toml or None if it could not be found.
    """
    path_project_root, _ = find_project_root(path_search_start)
    path_pyproject_toml = path_project_root / "pyproject.toml"
    if path_pyproject_toml.is_file():
        return str(path_pyproject_toml)

    return None


def parse_pyproject_toml(path_config: str) -> dict[str, Any]:
    """Parse a pyproject toml file, pulling out relevant parts for pymend.

    If parsing fails, will raise a tomllib.TOMLDecodeError.

    Parameters
    ----------
    path_config : str
        Path to the pyproject.toml file.

    Returns
    -------
    dict[str, Any]
        Configuration dictionary parsed from pyproject.toml
    """
    with open(path_config, "rb") as f:
        pyproject_toml: dict[str, Any] = tomllib.load(f)
    config: dict[str, Any] = pyproject_toml.get("tool", {}).get("pymend", {})
    return {k.replace("--", "").replace("-", "_"): v for k, v in config.items()}
