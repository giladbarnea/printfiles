#!/usr/bin/env python3
from __future__ import annotations

import sys
from typing import Callable

from .adapters.github import GitHubRepoSource
from .cli_common import derive_filters_and_print_flags, parse_common_args
from .core import DepthFirstPrinter, StdoutWriter
from .formatters import MarkdownFormatter, XmlFormatter


def main(url: str | None = None) -> None:
    parser, args = parse_common_args()
    # Special-case: first positional may be a GitHub URL; otherwise, require --repo
    if url is None:
        if not args.paths:
            parser.error("A GitHub repository URL must be provided as the first positional argument")
        url = args.paths[0]
        # After taking the URL, traverse from provided subpaths (relative to repo root),
        # default to repo root if none specified.
        args.paths = args.paths[1:] or [""]
    else:
        # URL was provided directly; keep any provided subpaths, or default to repo root
        args.paths = args.paths or [""]

    # Do not honor local .gitignore since we are traversing a remote repo
    args.no_ignore = True
    extensions, exclusions, include_empty, only_headers = derive_filters_and_print_flags(args)

    formatter = XmlFormatter() if args.tag == "xml" else MarkdownFormatter()
    source = GitHubRepoSource(url)
    printer = DepthFirstPrinter(
        source,
        formatter,
        include_empty=include_empty,
        only_headers=only_headers,
        extensions=extensions,
        exclude=exclusions,
    )

    writer = StdoutWriter()
    printer.run(args.paths, writer)


if __name__ == "__main__":
    # Keep a sane default on direct execution for smoke testing
    # If no argument provided, exit with usage guidance
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python -m printfiles.print_repo <github_repo_url> [options]\n")
        sys.exit(2)
    main(sys.argv[1])


def matches(argv: list[str]) -> bool:
    if not argv:
        return False
    first = argv[0].strip().lower()
    return (
        first.startswith("https://github.com/")
        or first.startswith("http://github.com/")
        or first.startswith("git+https://github.com/")
    )
