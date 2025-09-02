from __future__ import annotations

from .adapters.filesystem import FileSystemSource
from .cli_common import derive_filters_and_print_flags, parse_common_args
from .core import DepthFirstPrinter, StdoutWriter, Writer
from .formatters import MarkdownFormatter, XmlFormatter


def main(*, argv: list[str] | None = None, writer: Writer | None = None) -> None:
    _parser, args = parse_common_args(argv)
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
    out_writer = writer or StdoutWriter()
    printer.run(args.paths, out_writer)


def matches(argv: list[str]) -> bool:
    # Filesystem mode is the default fallback; always True.
    return True
