#!/usr/bin/env python3.12
import ast
import os
from collections.abc import Generator
from fnmatch import fnmatch
from pathlib import Path

# # We need both or neither, so we bunch them in a single try-except block.
# try:
#     from annotated_types import Predicate
#     from typeguard import typechecked
# except ImportError:
#     Predicate = lambda func: func  # type: ignore
#     typechecked = lambda func: func  # type: ignore
from typing import Any, TypeIs

from typeguard import typechecked

from prin.defaults import (
    DEFAULT_BINARY_EXCLUSIONS,
    DEFAULT_DOC_EXTENSIONS,
    DEFAULT_EXCLUSIONS,
    DEFAULT_LOCK_EXCLUSIONS,
    DEFAULT_SUPPORTED_EXTENSIONS,
    DEFAULT_TEST_EXCLUSIONS,
)
from prin.types import TExclusion, TExtension, TGlob, _is_extension, _is_glob


@typechecked
def is_glob(path) -> TypeIs[TGlob]:
    return _is_glob(path)


@typechecked
def is_extension(name: str) -> TypeIs[TExtension]:
    return _is_extension(name)


@typechecked
def print_single_file(
    file_path: Path,
    *,
    relative_to: Path | None = None,
    only_headers: bool,
    tag: str = "xml",
) -> None:
    """Print a single file's contents with header."""

    # Only print the relative path if the file is a subpath of the relative_to path.
    if relative_to and Path(relative_to).resolve() in [
        *Path(file_path).resolve().parents,
        Path(file_path).resolve(),
    ]:
        relative_path = os.path.relpath(file_path, start=relative_to)
    else:
        relative_path = str(file_path)

    try:
        with file_path.open("r", encoding="utf-8") as f:
            file_content = f.read().strip()
    except UnicodeDecodeError:
        with file_path.open("rb") as f:
            file_content = f.read().strip()

    if not file_content:
        import logging

        logging.getLogger(__name__).warning(
            "Shouldn't happen: %s is empty, but `depth_first_walk` should have filtered it out before this function was called. Investigation log: reproduced whenthere was an empty hi.md which matched and --include-empty was specified.",
            file_path,
        )
        return None

    if only_headers:
        print(relative_path)
    else:
        if tag == "xml":
            template = f"\n<{relative_path}>\n{file_content}\n</{relative_path}>\n\n"
        elif tag == "md":
            separator = "=" * (len(relative_path) + 8)
            template = f"\n# FILE: {{relative_path}}\n{separator}\n{{file_content}}\n\n---\n"
        else:
            msg = f"Unsupported tag format: {tag}"
            raise ValueError(msg)

        print(template.format(relative_path=relative_path, file_content=file_content))


@typechecked
def print_files_contents(
    root_dir,
    *,
    extensions: list[TExtension],
    exclude: list[TExclusion],
    only_headers: bool,
    include_empty: bool,
    tag: str = "xml",
) -> None:
    for root, _dirs, files in depth_first_walk(
        root_dir, exclude=exclude, include_empty=include_empty
    ):
        for file in files:
            # Check exclusions first
            if is_excluded(file, exclude=exclude):
                continue

            # Try to match the file against the extensions
            if any(
                fnmatch(file, extension_pattern)
                if is_glob(extension_pattern)
                else file.endswith("." + extension_pattern.removeprefix("."))
                for extension_pattern in extensions
            ):
                file_path = Path(root) / file
                print_single_file(
                    file_path,
                    relative_to=root_dir,
                    only_headers=only_headers,
                    tag=tag,
                )


@typechecked
def depth_first_walk(
    root_dir, *, exclude: list[TExclusion], include_empty: bool
) -> Generator[tuple[Path, list, list], Any, None]:
    def _append(_entry):
        if _entry.is_dir():
            dirs.append(_entry.name)
        elif _entry.is_file():
            files.append(_entry.name)

    stack = [root_dir]
    while stack:
        current_dir = Path(stack.pop())
        dirs, files = [], []
        entry: os.DirEntry[str]
        with os.scandir(current_dir) as entries:
            for entry in entries:
                if is_excluded(entry, exclude=exclude):
                    continue
                if include_empty:
                    considered_empty = False
                else:
                    considered_empty = is_empty(entry)

                if considered_empty:
                    continue

                _append(entry)
        dirs.sort(key=str.casefold)
        files.sort(key=str.casefold)
        yield current_dir, dirs, files
        stack.extend(current_dir / d for d in reversed(dirs))


@typechecked
def is_excluded(entry: os.DirEntry[str] | str | TGlob | Path, *, exclude: list[TExclusion]) -> bool:
    path = Path(getattr(entry, "path", entry))
    name = path.name
    stem = path.stem
    entry_is_glob = is_glob(entry)
    for _exclude in exclude:
        excluded_is_glob = entry_is_glob or is_glob(_exclude)
        if callable(_exclude):
            if _exclude(name) or _exclude(stem) or _exclude(str(path)):
                return True
        elif excluded_is_glob:
            if fnmatch(name, _exclude) or fnmatch(str(path), _exclude) or fnmatch(stem, _exclude):
                return True
        elif (
            name == _exclude
            or str(path) == _exclude
            or stem == _exclude
            or (is_extension(_exclude) and name.endswith(_exclude))
        ):
            return True
        else:
            _exclude_glob = f"*{_exclude}" if is_extension(_exclude) else f"*{_exclude}*"
            if (
                fnmatch(name, _exclude_glob)
                or fnmatch(str(path), _exclude_glob)
                or fnmatch(stem, _exclude_glob)
            ):
                return True
    return False


@typechecked
def is_empty(entry: os.DirEntry[str] | Path) -> bool:
    """Uses ast and returns True if the file only contains import statements, __all__=... assignment, and/or docstrings. Bug: doesn't handle comments (and shebang?)"""
    if isinstance(entry, os.DirEntry):
        if entry.is_dir():
            return False
        path = entry.path
    else:  # Path object
        if not entry.is_file():
            return False
        path = entry

    try:
        with Path(path).open("r", encoding="utf-8") as file:
            content = file.read()
    except UnicodeDecodeError:
        return False

    if not content.strip():
        return True

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return False

    # Files containing only imports, __all__=..., or docstrings are considered empty.
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        elif isinstance(node, ast.Assign):
            targets = node.targets
            if (
                len(targets) == 1
                and isinstance(targets[0], ast.Name)
                and targets[0].id == "__all__"
            ):
                continue
        elif (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            # This is a string expression (docstring)
            continue
        else:
            return False
    return True


@typechecked
def read_gitignore_file(gitignore_path: Path) -> list[TExclusion]:
    """Read a gitignore-like file and return list of exclusion patterns."""
    exclusions = []
    try:
        with gitignore_path.open("r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    exclusions.append(stripped)
    except (FileNotFoundError, UnicodeDecodeError, PermissionError):
        pass
    return exclusions


@typechecked
def get_gitignore_exclusions(paths: list[str]) -> list[TExclusion]:
    """Get exclusions from gitignore files for given paths."""
    exclusions = []

    # Read global git ignore file
    home_config_ignore = Path.home() / ".config" / "git" / "ignore"
    exclusions.extend(read_gitignore_file(home_config_ignore))

    # Read gitignore files for each directory path
    for path_str in paths:
        path = Path(path_str)
        if path.is_dir():
            # Try .gitignore in the directory
            gitignore_path = path / ".gitignore"
            exclusions.extend(read_gitignore_file(gitignore_path))

            # Try .git/info/exclude in the directory
            git_exclude_path = path / ".git" / "info" / "exclude"
            exclusions.extend(read_gitignore_file(git_exclude_path))

    return exclusions


@typechecked
def resolve_exclusions(
    *,
    no_exclude: bool,
    custom_excludes: list[TExclusion],
    include_tests: bool,
    include_lock: bool,
    include_binary: bool,
    no_ignore: bool,
    paths: list[str],
) -> list[TExclusion]:
    """
    Resolve final exclusion list based on command line arguments.
    Smell: generic logic that should be moved somewhere common."""
    if no_exclude:
        return []

    exclusions = DEFAULT_EXCLUSIONS.copy()
    exclusions.extend(custom_excludes)

    if not include_tests:
        exclusions.extend(DEFAULT_TEST_EXCLUSIONS)

    if not include_lock:
        exclusions.extend(DEFAULT_LOCK_EXCLUSIONS)

    if not include_binary:
        exclusions.extend(DEFAULT_BINARY_EXCLUSIONS)

    if not no_ignore:
        exclusions.extend(get_gitignore_exclusions(paths))
    return exclusions


@typechecked
def resolve_extensions(
    *,
    custom_extensions: list[str],
    no_docs: bool,
) -> list[str]:
    """Resolve final extension list based on command line arguments."""
    if custom_extensions:
        extensions = custom_extensions
    else:
        extensions = DEFAULT_SUPPORTED_EXTENSIONS
        if not no_docs:
            extensions.extend(DEFAULT_DOC_EXTENSIONS)

    return extensions


def main():
    # Reuse shared CLI to avoid duplication
    from .adapters.filesystem import FileSystemSource
    from .cli_common import derive_filters_and_print_flags, parse_common_args
    from .core import DepthFirstPrinter, StdoutWriter
    from .formatters import MarkdownFormatter, XmlFormatter

    _parser, args = parse_common_args()
    extensions, exclusions, include_empty, only_headers = derive_filters_and_print_flags(args)

    formatter = XmlFormatter() if args.tag == "xml" else MarkdownFormatter()
    printer = DepthFirstPrinter(
        FileSystemSource(),
        formatter,
        include_empty=include_empty,
        only_headers=only_headers,
        extensions=extensions,
        exclude=exclusions,
    )
    printer.run(args.paths, StdoutWriter())


if __name__ == "__main__":
    main()


def matches(argv: list[str]) -> bool:
    # Filesystem mode is the default fallback; always True.
    return True
