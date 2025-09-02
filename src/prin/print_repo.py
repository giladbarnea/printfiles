#!/usr/bin/env python3
from __future__ import annotations

import sys

from .adapters.github import GitHubRepoSource
from .cli_common import derive_filters_and_print_flags, parse_common_args
from .core import DepthFirstPrinter, StdoutWriter, StringWriter
from .defaults import DEFAULT_TAG
from .formatters import MarkdownFormatter, XmlFormatter
from .util import extract_in_repo_subpath, is_github_url


def main(url: str | None = None) -> None:
    parser, args = parse_common_args()
    # Special-case: first positional may be a GitHub URL; otherwise, require --repo
    if url is None:
        if not args.paths:
            parser.error(
                "A GitHub repository URL must be provided as the first positional argument"
            )
        url = args.paths[0]
        # Derive the initial root from the URL itself, supporting optional blob/ and main|master/ segments
        derived_root = extract_in_repo_subpath(url).strip("/")
        extra_roots = args.paths[1:]
        paths: list[str] = []
        if derived_root:
            paths.append(derived_root)
        paths.extend(extra_roots)
        if not paths:
            paths = [""]
        args.paths = paths
    else:
        # URL was provided directly; use any provided subpaths, or derive from URL, or default to repo root
        derived_root = extract_in_repo_subpath(url).strip("/")
        if args.paths:
            pass  # honor provided paths as-is
        elif derived_root:
            args.paths = [derived_root]
        else:
            args.paths = [""]

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


def render_repo(
    url: str,
    subpaths: list[str] | None = None,
    *,
    tag: str = DEFAULT_TAG,
    include_empty: bool | None = None,
    only_headers: bool | None = None,
    extensions: list[str] | None = None,
    exclude: list | None = None,
) -> str:
    """
    Render a GitHub repo (optionally a subpath) to a single string.

    Mirrors CLI defaults and semantics used by `main()`, but returns the
    full output as a string so tests can import and assert without custom
    buffer helpers or stdout capture.
    - URL may embed an in-repo path (supports optional blob/ and main|master/).
    - `subpaths` can add additional roots (relative to repo root).
    - Ignores local gitignore files by design (remote repo traversal).
    """
    # Derive roots like the CLI does
    derived = extract_in_repo_subpath(url).strip("/")
    roots: list[str] = []
    if derived:
        roots.append(derived)
    if subpaths:
        roots.extend(subpaths)
    if not roots:
        roots = [""]

    # Resolve filters with the shared helpers to ensure parity with CLI
    from .filters import resolve_exclusions, resolve_extensions

    # Defaults match CLI behavior unless explicitly overridden
    exts = (
        extensions
        if extensions is not None
        else resolve_extensions(custom_extensions=[], no_docs=False)
    )
    exc = (
        exclude
        if exclude is not None
        else resolve_exclusions(
            no_exclude=False,
            custom_excludes=[],
            include_tests=False,
            include_lock=False,
            include_binary=False,
            no_ignore=True,  # critical: remote repo should not consult local gitignore
            paths=roots,
        )
    )
    inc_empty = bool(include_empty) if include_empty is not None else False
    headers_only = bool(only_headers) if only_headers is not None else False

    formatter = XmlFormatter() if tag == "xml" else MarkdownFormatter()
    source = GitHubRepoSource(url)
    printer = DepthFirstPrinter(
        source,
        formatter,
        include_empty=inc_empty,
        only_headers=headers_only,
        extensions=exts,
        exclude=exc,
    )
    buf = StringWriter()
    printer.run(roots, buf)
    return buf.text()


if __name__ == "__main__":
    # Keep a sane default on direct execution for smoke testing
    # If no argument provided, exit with usage guidance
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python -m prin.print_repo <github_repo_url> [options]\n")
        sys.exit(2)
    main(sys.argv[1])


def matches(argv: list[str]) -> bool:
    if not argv:
        return False
    return any(is_github_url(tok) for tok in argv)
