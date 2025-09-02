from __future__ import annotations

from .adapters.github import GitHubRepoSource
from .cli_common import derive_filters_and_print_flags, parse_common_args
from .core import DepthFirstPrinter, StdoutWriter, Writer
from .defaults import DEFAULT_RUN_PATH
from .formatters import MarkdownFormatter, XmlFormatter
from .util import extract_in_repo_subpath, is_github_url


def main(
    url: str | None = None,
    subpaths: list[str] | None = None,
    *,
    argv: list[str] | None = None,
    writer: Writer | None = None,
) -> None:
    _parser, args = parse_common_args(argv)
    # Special-case: first positional may be a GitHub URL; otherwise, require --repo
    if url is None:
        if not args.paths:
            raise ValueError(
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
        if args.paths and args.paths != [DEFAULT_RUN_PATH]:
            pass  # honor provided paths as-is
        elif derived_root:
            args.paths = [derived_root]
        else:
            args.paths = [""]

    # Allow explicit subpaths from caller (tests) to be appended
    if subpaths:
        args.paths.extend(subpaths)

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

    out_writer = writer or StdoutWriter()
    printer.run(args.paths, out_writer)


def matches(argv: list[str]) -> bool:
    if not argv:
        return False
    return any(is_github_url(tok) for tok in argv)
