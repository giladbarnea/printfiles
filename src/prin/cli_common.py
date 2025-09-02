from __future__ import annotations

import argparse
import textwrap
from typing import Tuple

from prin.defaults import (
    DEFAULT_EXCLUDE_FILTER,
    DEFAULT_EXCLUSIONS,
    DEFAULT_EXTENSIONS_FILTER,
    DEFAULT_INCLUDE_BINARY,
    DEFAULT_INCLUDE_EMPTY,
    DEFAULT_INCLUDE_LOCK,
    DEFAULT_INCLUDE_TESTS,
    DEFAULT_NO_DOCS,
    DEFAULT_NO_EXCLUDE,
    DEFAULT_NO_IGNORE,
    DEFAULT_ONLY_HEADERS,
    DEFAULT_RUN_PATH,
    DEFAULT_TAG,
    DEFAULT_TAG_CHOICES,
)
from prin.types import _describe_predicate

# Intentionally avoid importing from print_files at module import time to
# prevent circular imports. We'll import lazily inside functions.


def parse_common_args(
    argv: list[str] | None = None,
) -> Tuple[argparse.ArgumentParser, argparse.Namespace]:
    # Lazy imports from the reference implementation
    from .print_files import (
        resolve_extensions,  # type: ignore
    )

    epilog = textwrap.dedent(
        f"""
        DEFAULT MATCH CRITERIA
        When -e,--extension is unspecified, the following file extensions are matched: {", ".join(resolve_extensions(custom_extensions=[], no_docs=False))}.

        NOTE ABOUT EXCLUSIONS
        Exclusions match rather eagerly, because each specified exclusion is handled like a substring match. For example, 'o/b' matches 'foo/bar/baz'.
        Extension exclusions are stricter, so '.py' matches 'foo.py' but not 'foo.pyc'.
        For more control, use glob patterns; specifying '*o/b' will match 'foo/b' but not 'foo/bar/baz'.
        """
    )

    parser = argparse.ArgumentParser(
        description="Prints the contents of files in a directory or specific file paths",
        add_help=True,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )

    parser.add_argument(
        "paths",
        type=str,
        nargs="*",
        help="Path(s) or roots. Defaults to current directory if none specified.",
        default=[DEFAULT_RUN_PATH],
    )

    # Uppercase short flags are boolean "include" flags.
    parser.add_argument(
        "-T",
        "--include-tests",
        action="store_true",
        help="Include `test` and `tests` directories and spec.ts files.",
        default=DEFAULT_INCLUDE_TESTS,
    )
    parser.add_argument(
        "-K",
        "--include-lock",
        action="store_true",
        help="Include lock files (e.g. package-lock.json, poetry.lock, Cargo.lock).",
        default=DEFAULT_INCLUDE_LOCK,
    )
    parser.add_argument(
        "-a",
        "--text",
        "--include-binary",
        "--binary",
        action="store_true",
        dest="include_binary",
        help="Include binary files (e.g. *.pyc, *.jpg, *.zip, *.pdf).",
        default=DEFAULT_INCLUDE_BINARY,
    )
    parser.add_argument(
        "-d",
        "--no-docs",
        action="store_true",
        help="Exclude `.md`, `.mdx` and `.rst` files. Has no effect if -e,--extension is specified.",
        default=DEFAULT_NO_DOCS,
    )
    parser.add_argument(
        "-M",
        "--include-empty",
        action="store_true",
        help="Include empty files and files that only contain imports and __all__=... expressions.",
        default=DEFAULT_INCLUDE_EMPTY,
    )
    parser.add_argument(
        "-l",
        "--only-headers",
        action="store_true",
        help="Print only the file paths.",
        default=DEFAULT_ONLY_HEADERS,
    )
    parser.add_argument(
        "-e",
        "--extension",
        type=str,
        default=DEFAULT_EXTENSIONS_FILTER,
        action="append",
        help="Only include files with the given extension (repeatable).",
    )

    parser.add_argument(
        "-E",
        "--exclude",
        "--ignore",
        type=str,
        help="Exclude files or directories by shell-style glob or regex (repeatable). By default, excludes "
        + ", ".join(map(_describe_predicate, DEFAULT_EXCLUSIONS))
        + ", and any files in .gitignore, .git/info/exclude, and ~/.config/git/ignore.",
        default=DEFAULT_EXCLUDE_FILTER,
        action="append",
    )
    parser.add_argument(
        "--no-exclude",
        action="store_true",
        help="Disable all exclusions (overrides --exclude).",
        default=DEFAULT_NO_EXCLUDE,
    )
    parser.add_argument(
        "-I",
        "--no-ignore",
        action="store_true",
        help="Disable gitignore file processing.",
        default=DEFAULT_NO_IGNORE,
    )
    parser.add_argument(
        "--tag",
        type=str,
        choices=DEFAULT_TAG_CHOICES,
        default=DEFAULT_TAG,
        help="Output format tag: 'xml' or 'md'.",
    )

    args = parser.parse_args(argv)
    return parser, args


def derive_filters_and_print_flags(args) -> tuple[list[str], list, bool, bool]:
    # Lazy import to avoid cycles
    from .print_files import resolve_exclusions, resolve_extensions  # type: ignore

    extensions = resolve_extensions(custom_extensions=args.extension, no_docs=args.no_docs)
    exclusions = resolve_exclusions(
        no_exclude=args.no_exclude,
        custom_excludes=args.exclude,
        include_tests=args.include_tests,
        include_lock=args.include_lock,
        include_binary=args.include_binary,
        no_ignore=args.no_ignore,
        paths=args.paths,
    )
    return extensions, exclusions, bool(args.include_empty), bool(args.only_headers)
