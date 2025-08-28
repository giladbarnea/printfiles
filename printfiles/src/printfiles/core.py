from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import PurePosixPath
from typing import Callable, Iterable, Protocol


class NodeKind(Enum):
    DIRECTORY = auto()
    FILE = auto()
    OTHER = auto()


@dataclass(frozen=True)
class Entry:
    path: PurePosixPath
    name: str
    kind: NodeKind


class Writer(Protocol):
    def write(self, text: str) -> None: ...


class SourceAdapter(Protocol):
    def resolve_root(self, root_spec: str) -> PurePosixPath: ...
    def list_dir(self, dir_path: PurePosixPath) -> Iterable[Entry]: ...
    def read_file_bytes(self, file_path: PurePosixPath) -> bytes: ...
    def is_empty(self, file_path: PurePosixPath) -> bool: ...


class Formatter(Protocol):
    def body(self, path: str, text: str) -> str: ...
    def binary(self, path: str) -> str: ...
    def header(self, path: str) -> str: ...


def is_text_semantically_empty(text: str) -> bool:
    """Return True if text contains only imports, __all__=..., or docstrings.

    Mirrors the behavior used by the filesystem implementation.
    """
    import ast

    if not text.strip():
        return True

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        elif isinstance(node, ast.Assign):
            targets = node.targets
            if (
                len(targets) == 1
                and isinstance(targets[0], ast.Name)
                and targets[0].id == "__all__"
            ):
                continue
        elif (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            # Docstring
            continue
        else:
            return False
    return True


def _is_text_bytes(blob: bytes) -> bool:
    if not blob:
        return True
    if b"\x00" in blob:
        return False
    try:
        blob.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def _decode_text(blob: bytes) -> str:
    try:
        return blob.decode("utf-8")
    except UnicodeDecodeError:
        return blob.decode("latin-1")


class StdoutWriter:
    def write(self, text: str) -> None:
        sys.stdout.write(text)


class DepthFirstPrinter:
    def __init__(
        self,
        source: SourceAdapter,
        formatter: Formatter,
        *,
        include_empty: bool,
        only_headers: bool,
        extensions: list[str],
        exclude: list,
    ) -> None:
        self.source = source
        self.formatter = formatter
        self.include_empty = include_empty
        self.only_headers = only_headers
        self.extensions = extensions
        self.exclude = exclude

        # Import filtering primitives from the reference implementation
        # to preserve semantics exactly.
        from . import print_files as pf  # type: ignore

        self._pf_is_excluded: Callable[[object, list], bool] = pf.is_excluded
        self._pf_is_glob: Callable[[object], bool] = pf._is_glob  # type: ignore[attr-defined]

    def run(self, roots: list[str], writer: Writer) -> None:
        from . import print_files as pf  # lazy import for safety

        for root_spec in roots or ["."]:
            root = self.source.resolve_root(root_spec)
            stack: list[PurePosixPath] = [root]
            while stack:
                current = stack.pop()
                try:
                    entries = list(self.source.list_dir(current))
                except NotADirectoryError:
                    # Treat the current path as a file
                    file_entry = Entry(path=current, name=current.name, kind=NodeKind.FILE)
                    self._handle_file(file_entry, writer)
                    continue
                except FileNotFoundError:
                    # Skip missing paths
                    continue
                # Sort directories then files, both case-insensitive
                dirs = [e for e in entries if e.kind is NodeKind.DIRECTORY]
                files = [e for e in entries if e.kind is NodeKind.FILE]
                dirs.sort(key=lambda e: e.name.casefold())
                files.sort(key=lambda e: e.name.casefold())

                for entry in reversed(dirs):  # reversed for stack DFS order
                    if not self._excluded(entry):
                        stack.append(entry.path)

                for entry in files:
                    self._handle_file(entry, writer)

    def _excluded(self, entry: Entry) -> bool:
        # The reference implementation accepts strings/paths/globs/callables
        return self._pf_is_excluded(str(entry.path), exclude=self.exclude)

    def _extension_match(self, filename: str) -> bool:
        if not self.extensions:
            return True
        for pattern in self.extensions:
            if self._pf_is_glob(pattern):
                from fnmatch import fnmatch

                if fnmatch(filename, pattern):
                    return True
            else:
                if filename.endswith("." + pattern.removeprefix(".")):
                    return True
        return False

    def _handle_file(self, entry: Entry, writer: Writer) -> None:
        if self._excluded(entry):
            return
        if not self._extension_match(entry.name):
            return

        if not self.include_empty and self.source.is_empty(entry.path):
            return

        path_str = str(entry.path)
        if self.only_headers:
            writer.write(self.formatter.header(path_str))
            return

        blob = self.source.read_file_bytes(entry.path)
        if _is_text_bytes(blob):
            text = _decode_text(blob)
            writer.write(self.formatter.body(path_str, text))
        else:
            writer.write(self.formatter.binary(path_str))

