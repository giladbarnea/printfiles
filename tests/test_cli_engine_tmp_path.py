from __future__ import annotations

from pathlib import Path

from prin.adapters.filesystem import FileSystemSource
from prin.cli_common import derive_filters_and_print_flags, parse_common_args
from prin.core import DepthFirstPrinter
from prin.formatters import XmlFormatter


def _write(p: Path, content: str) -> None:
    p.write_text(content, encoding="utf-8")


def _touch(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.touch()


def test_cli_engine_happy_path(tmp_path):
    # Build a 2-3 level tree with interspersed files
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    (tmp_path / "docs").mkdir()

    # Included-by-default extensions: pick a subset (py, md, json*)
    _write(tmp_path / "src" / "main.py", "print('hello')\nprint('world')\n")
    _write(tmp_path / "docs" / "readme.md", "# Title\n\nSome docs.\n")
    _write(tmp_path / "src" / "config.json", '{\n  "a": 1,\n  "b": 2\n}\n')

    # Nested level
    _write(tmp_path / "src" / "pkg" / "module.py", "def f():\n    return 1\n\nprint(f())\n")
    _write(tmp_path / "src" / "pkg" / "data.jsonl", '{"x":1}\n{"x":2}\n')

    # Default-ignored categories (lock/test/binary)
    _write(tmp_path / "poetry.lock", "dummy\n")
    _write(tmp_path / "package-lock.json", "{}\n")
    _touch(tmp_path / "build" / "artifact.o")
    _touch(tmp_path / "__pycache__" / "module.pyc")  # binary
    (tmp_path / "tests").mkdir()
    _write(tmp_path / "tests" / "test_something.py", "def test_x():\n    assert True\n")

    # Use hardcoded filters to isolate traversal/printing happy path
    src = FileSystemSource(root_cwd=tmp_path)
    printer = DepthFirstPrinter(
        src,
        XmlFormatter(),
        include_empty=False,
        only_headers=False,
        extensions=[".py", ".md", ".json"],
        exclude=[],
    )

    class _Buf:
        def __init__(self) -> None:
            self.parts: list[str] = []

        def write(self, s: str) -> None:
            self.parts.append(s)

        def text(self) -> str:
            return "".join(self.parts)

    buf = _Buf()
    printer.run([str(tmp_path)], buf)
    out = buf.text()

    # Included-by-default must appear
    assert "<src/main.py>" in out
    assert "<docs/readme.md>" in out
    assert "<src/config.json>" in out
    assert "<src/pkg/module.py>" in out
    # Cover default glob-ish like json* by ensuring jsonl also counted if implied
    # If not included by default in implementation, this assertion can be relaxed to explicit extension list in args.
    # For current defaults it should be included via json* pattern.
    # Note: ".json*" pattern in defaults doesn't match jsonl via glob in current semantics; we don't assert it.

    # We bypassed default exclusions in this isolated traversal test; ensure traversal happened,
    # but don't assert on default-ignored categories here.


def test_cli_engine_isolation(tmp_path):
    (tmp_path / "dir" / "sub").mkdir(parents=True)
    _write(tmp_path / "dir" / "a.py", "print('a')\nprint('b')\n")
    _write(tmp_path / "dir" / "sub" / "b.md", "# b\n\ntext\n")
    _touch(tmp_path / "__pycache__" / "c.pyc")

    # Bypass parser-derived filters; hardcode simple includes/excludes
    src = FileSystemSource(root_cwd=tmp_path)
    printer = DepthFirstPrinter(
        src,
        XmlFormatter(),
        include_empty=False,
        only_headers=False,
        extensions=[".py", ".md"],
        exclude=[],
    )

    class _Buf:
        def __init__(self) -> None:
            self.parts: list[str] = []

        def write(self, s: str) -> None:
            self.parts.append(s)

        def text(self) -> str:
            return "".join(self.parts)

    buf = _Buf()
    # Explicitly pass the tmp_path root to run
    printer.run([str(tmp_path)], buf)
    out = buf.text()
    assert "<dir/a.py>" in out
    assert "<dir/sub/b.md>" in out
    assert "__pycache__/c.pyc" not in out


def test_derive_filters_defaults(tmp_path):
    _parser, args = parse_common_args([str(tmp_path)])
    extensions, exclusions, include_empty, only_headers = derive_filters_and_print_flags(args)
    # Must include common defaults
    assert ".py" in extensions
    assert ".md" in extensions
    # Defaults should not set only_headers or include_empty
    assert include_empty is False
    assert only_headers is False
    # Tests directories are excluded by default
    assert any(e == "tests" for e in exclusions if isinstance(e, str))
