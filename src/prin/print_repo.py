#!/usr/bin/env python3
from __future__ import annotations

import sys
from urllib.parse import urlparse

from .adapters.github import GitHubRepoSource
from .cli_common import derive_filters_and_print_flags, parse_common_args
from .core import DepthFirstPrinter, StdoutWriter
from .formatters import MarkdownFormatter, XmlFormatter


def _extract_in_repo_subpath(url: str) -> str:
    """Return the path inside the repo from a GitHub URL.

    Examples we accept (all equivalent w.r.t. subpath extraction):
    - https://github.com/<owner>/<repo>/blob/<branch>/dir/file
    - https://github.com/<owner>/<repo>/<branch>/dir/file
    - https://github.com/<owner>/<repo>/blob/dir/file
    - https://github.com/<owner>/<repo>/dir/file

    Rules:
    - Strip an initial 'blob/' segment if present.
    - Strip an initial 'main/' or 'master/' segment if present (whether or not 'blob/' preceded it).
    - Everything after these optional segments is treated as the subpath (may be empty for repo root).
    """
    parsed = urlparse(url)
    # parsed.path: "/<owner>/<repo>[/...]"
    raw_path = (parsed.path or "").strip("/")
    if not raw_path:
        return ""
    segments = raw_path.split("/")
    # Require owner/repo at minimum
    if len(segments) < 2:
        return ""
    rest = segments[2:]
    if not rest:
        return ""
    # Remove optional 'blob' segment
    if rest and rest[0] == "blob":
        rest = rest[1:]
    # Remove optional default branch markers
    if rest and rest[0] in {"main", "master"}:
        rest = rest[1:]
    return "/".join(rest)


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
        derived_root = _extract_in_repo_subpath(url).strip("/")
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
        derived_root = _extract_in_repo_subpath(url).strip("/")
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
    first = argv[0].strip().lower()
    return (
        first.startswith("https://github.com/")
        or first.startswith("http://github.com/")
        or first.startswith("git+https://github.com/")
    )
