#!/usr/bin/env python3.12
from __future__ import annotations

from .adapters.filesystem import FileSystemSource
from .cli_common import derive_filters_and_print_flags, parse_common_args
from .core import DepthFirstPrinter, StdoutWriter
from .formatters import MarkdownFormatter, XmlFormatter


def main() -> None:
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
