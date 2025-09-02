from __future__ import annotations

from pathlib import Path

from prin.adapters.filesystem import FileSystemSource
from prin.core import DepthFirstPrinter
from prin.formatters import XmlFormatter


def _write(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _touch(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.touch()


def _run(src: FileSystemSource, roots: list[str]) -> str:
    class _Buf:
        def __init__(self) -> None:
            self.parts: list[str] = []

        def write(self, s: str) -> None:
            self.parts.append(s)

        def text(self) -> str:
            return "".join(self.parts)

    buf = _Buf()
    printer = DepthFirstPrinter(
        src,
        XmlFormatter(),
        include_empty=True,
        only_headers=False,
        extensions=[".py", ".md", ".json"],
        exclude=["__pycache__", "*.pyc", "build", "dist", "*.o", "*.so"],
    )
    printer.run(roots, buf)
    return buf.text()


def test_explicit_single_ignored_file_is_printed(tmp_path: Path):
    # Create an ignored-by-default file (e.g., binary-like or lock)
    lock = tmp_path / "poetry.lock"
    _write(lock, "dummy\n")
    out = _run(FileSystemSource(root_cwd=tmp_path), [str(lock)])
    assert "<poetry.lock>" in out


def test_two_sibling_directories(tmp_path: Path):
    # dirA and dirB siblings, each with printable files
    _write(tmp_path / "dirA" / "a.py", "print('a')\n")
    _write(tmp_path / "dirB" / "b.md", "# b\n")
    out = _run(
        FileSystemSource(root_cwd=tmp_path), [str(tmp_path / "dirA"), str(tmp_path / "dirB")]
    )
    # Paths are relative to each provided root
    assert "<a.py>" in out
    assert "<b.md>" in out


def test_directory_and_explicit_ignored_file_inside(tmp_path: Path):
    # directory contains mixed files; specify dir and an otherwise-ignored file
    _write(tmp_path / "work" / "keep.py", "print('ok')\n")
    _touch(tmp_path / "work" / "__pycache__" / "junk.pyc")
    # Explicitly pass both the directory and the ignored file path
    out = _run(
        FileSystemSource(root_cwd=tmp_path),
        [str(tmp_path / "work"), str(tmp_path / "work" / "__pycache__" / "junk.pyc")],
    )
    # Paths are relative to the directory root when provided
    assert "<keep.py>" in out
    # Even though *.pyc is excluded by default, explicit root forces print
    assert "<junk.pyc>" in out or "<work/__pycache__/junk.pyc>" in out
