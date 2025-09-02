from __future__ import annotations

from pathlib import Path

from prin.adapters.filesystem import FileSystemSource
from prin.cli_common import Context, derive_filters_and_print_flags, parse_common_args
from prin.core import DepthFirstPrinter, StringWriter
from prin.formatters import XmlFormatter
from tests.utils import touch_file as _touch, write_text_file as _write


def test_cli_engine_happy_path(tmp_path: Path, comprehensive_fs: Path):
    # Use the session-scoped comprehensive filesystem as the root to exercise traversal
    src = FileSystemSource(root_cwd=comprehensive_fs)
    printer = DepthFirstPrinter(
        src,
        XmlFormatter(),
        include_empty=False,
        only_headers=False,
        extensions=[".py", ".md", ".json"],
        exclude=[],
    )

    buf = StringWriter()
    printer.run([str(comprehensive_fs)], buf)
    out = buf.text()

    # Included-by-default must appear
    assert "<src/main.py>" in out
    assert "<docs/readme.md>" in out
    assert "<src/config.json>" in out
    assert "<src/pkg/module.py>" in out



def test_cli_engine_isolation(tmp_path: Path):
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

    buf = StringWriter()
    # Explicitly pass the tmp_path root to run
    printer.run([str(tmp_path)], buf)
    out = buf.text()
    assert "<dir/a.py>" in out
    assert "<dir/sub/b.md>" in out
    assert "__pycache__/c.pyc" not in out



def test_derive_filters_defaults(tmp_path: Path):
    ctx: Context = parse_common_args([str(tmp_path)])
    extensions, exclusions, include_empty, only_headers = derive_filters_and_print_flags(ctx)
    # Must include common defaults
    assert ".py" in extensions
    assert ".md" in extensions
    # Defaults should not set only_headers or include_empty
    assert include_empty is False
    assert only_headers is False
    # Tests directories are excluded by default
    assert any(e == "tests" for e in exclusions if isinstance(e, str))
