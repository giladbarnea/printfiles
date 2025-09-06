from __future__ import annotations

from .adapters.github import GitHubRepoSource
from .cli_common import Context, derive_filters_and_print_flags, parse_common_args
from .core import DepthFirstPrinter, FileBudget, StdoutWriter, Writer
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
    ctx: Context = parse_common_args(argv)
    # Special-case: first positional may be a GitHub URL; otherwise, require --repo
    if url is None:
        if not ctx.paths:
            raise ValueError(
                "A GitHub repository URL must be provided as the first positional argument"
            )
        url = ctx.paths[0]
        # Derive the initial root from the URL itself, supporting optional blob/ and main|master/ segments
        derived_root = extract_in_repo_subpath(url).strip("/")
        extra_roots = ctx.paths[1:]
        paths: list[str] = []
        if derived_root:
            paths.append(derived_root)
        paths.extend(extra_roots)
        if not paths:
            paths = [""]
        ctx.paths = paths
    else:
        # URL was provided directly; use any provided subpaths, or derive from URL, or default to repo root
        derived_root = extract_in_repo_subpath(url).strip("/")
        if ctx.paths and ctx.paths != [DEFAULT_RUN_PATH]:
            pass  # honor provided paths as-is
        elif derived_root:
            ctx.paths = [derived_root]
        else:
            ctx.paths = [""]

    # Allow explicit subpaths from caller (tests) to be appended
    if subpaths:
        ctx.paths.extend(subpaths)

    # Do not honor local .gitignore since we are traversing a remote repo
    ctx.no_ignore = True
    extensions, exclusions, include_empty, only_headers = derive_filters_and_print_flags(ctx)

    formatter = XmlFormatter() if ctx.tag == "xml" else MarkdownFormatter()
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
    budget = FileBudget(ctx.max_files)
    printer.run(ctx.paths, out_writer, budget=budget)


def matches(argv: list[str]) -> bool:
    if not argv:
        return False
    return any(is_github_url(tok) for tok in argv)
