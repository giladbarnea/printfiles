from __future__ import annotations

import argparse
import textwrap
from typing import Tuple

# Intentionally avoid importing from print_files at module import time to
# prevent circular imports. We'll import lazily inside functions.


def parse_common_args(argv: list[str] | None = None) -> Tuple[argparse.ArgumentParser, argparse.Namespace]:
    # Lazy imports from the reference implementation
    from .print_files import (
        resolve_extensions,  # type: ignore
    )

    epilog = textwrap.dedent(
        f"""
        DEFAULT MATCH CRITERIA
        When -t,--type is unspecified, the following file extensions are matched: {', '.join(resolve_extensions(custom_extensions=[], no_docs=False))}.

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
        default=["."],
    )

    # Uppercase short flags are boolean "include" flags.
    parser.add_argument("-T", "--include-tests", action="store_true", help="Include `test` and `tests` directories and spec.ts files.")
    parser.add_argument("-L", "--include-lock", action="store_true", help="Include lock files (e.g. package-lock.json, poetry.lock, Cargo.lock).")
    parser.add_argument("-a", "--text", "--include-binary", "--binary", action="store_true", dest="include_binary", help="Include binary files (e.g. *.pyc, *.jpg, *.zip, *.pdf).")
    parser.add_argument("-d", "--no-docs", action="store_true", help="Exclude `.md`, `.mdx` and `.rst` files. Has no effect if -t,--type is specified.")
    parser.add_argument("-E", "--include-empty", action="store_true", help="Include empty files and files that only contain imports and __all__=... expressions.")
    parser.add_argument("-l", "--only-headers", action="store_true", help="Print only the file paths.")
    parser.add_argument("-t", "--type", type=str, default=[], action="append", help="Match only files with the given extensions or glob patterns. Can be specified multiple times.")
    # Lazy import remaining helpers for help text
    from .print_files import (
        DEFAULT_EXCLUSIONS,  # type: ignore
        _describe_predicate,  # type: ignore
    )

    parser.add_argument(
        "-x",
        "--exclude",
        type=str,
        help="Exclude files or directories whose path contains the given name/path or matches the given glob. Can be specified multiple times. By default, excludes "
        + ", ".join(map(_describe_predicate, DEFAULT_EXCLUSIONS))
        + ", and any files in .gitignore, .git/info/exclude, and ~/.config/git/ignore.",
        default=[],
        action="append",
    )
    parser.add_argument("--no-exclude", action="store_true", help="Disable all exclusions (overrides --exclude).")
    parser.add_argument("-I", "--no-ignore", action="store_true", help="Disable gitignore file processing.")
    parser.add_argument("--tag", type=str, choices=["xml", "md"], default="xml", help="Output format tag: 'xml' or 'md'.")

    args = parser.parse_args(argv)
    return parser, args


def derive_filters_and_print_flags(args) -> tuple[list[str], list, bool, bool]:
    # Lazy import to avoid cycles
    from .print_files import resolve_extensions, resolve_exclusions  # type: ignore

    extensions = resolve_extensions(custom_extensions=args.type, no_docs=args.no_docs)
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

