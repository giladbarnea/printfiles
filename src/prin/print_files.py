from __future__ import annotations

from .adapters.filesystem import FileSystemSource
from .cli_common import Context, derive_filters_and_print_flags, parse_common_args
from .core import DepthFirstPrinter, PrintBudget, StdoutWriter, Writer
from .formatters import MarkdownFormatter, XmlFormatter


def main(*, argv: list[str] | None = None, writer: Writer | None = None) -> None:
    ctx: Context = parse_common_args(argv)
    extensions, exclusions, include_empty, only_headers = derive_filters_and_print_flags(ctx)

    formatter = XmlFormatter() if ctx.tag == "xml" else MarkdownFormatter()
    printer = DepthFirstPrinter(
        FileSystemSource(),
        formatter,
        include_empty=include_empty,
        only_headers=only_headers,
        extensions=extensions,
        exclude=exclusions,
    )
    out_writer = writer or StdoutWriter()
    budget = PrintBudget(ctx.max_files)
    printer.run(ctx.paths, out_writer, budget=budget)


def matches(argv: list[str]) -> bool:
    # Filesystem mode is the default fallback; always True.
    return True
