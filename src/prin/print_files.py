#!/usr/bin/env python3.12
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

from prin.types import TExclusion, TExtension, TGlob

from .core import is_text_semantically_empty
from .filters import (
    is_excluded as _shared_is_excluded,
)
from .filters import (
    is_extension as _shared_is_extension,
)
from .filters import (
    is_glob as _shared_is_glob,
)
from .filters import (
    resolve_exclusions as _shared_resolve_exclusions,
)
from .filters import (
    resolve_extensions as _shared_resolve_extensions,
)


@typechecked
def is_glob(path) -> TypeIs[TGlob]:
    # Backwards-compat wrapper
    return _shared_is_glob(path)


@typechecked
def is_extension(name: str) -> TypeIs[TExtension]:
    # Backwards-compat wrapper
    return _shared_is_extension(name)


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
    # Backwards-compat wrapper to shared filters
    return _shared_is_excluded(entry, exclude=exclude)


@typechecked
def is_empty(entry: os.DirEntry[str] | Path) -> bool:
    """Return True if the file is semantically empty (imports, __all__, docstrings)."""
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
    return is_text_semantically_empty(content)


@typechecked
def read_gitignore_file(gitignore_path: Path) -> list[TExclusion]:
    # Backwards-compat wrapper
    from .filters import read_gitignore_file as _read

    return _read(gitignore_path)


@typechecked
def get_gitignore_exclusions(paths: list[str]) -> list[TExclusion]:
    # Backwards-compat wrapper
    from .filters import get_gitignore_exclusions as _gg

    return _gg(paths)


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
    # Backwards-compat wrapper
    return _shared_resolve_exclusions(
        no_exclude=no_exclude,
        custom_excludes=custom_excludes,
        include_tests=include_tests,
        include_lock=include_lock,
        include_binary=include_binary,
        no_ignore=no_ignore,
        paths=paths,
    )


@typechecked
def resolve_extensions(
    *,
    custom_extensions: list[str],
    no_docs: bool,
) -> list[str]:
    # Backwards-compat wrapper
    return _shared_resolve_extensions(custom_extensions=custom_extensions, no_docs=no_docs)


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
