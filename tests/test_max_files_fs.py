from __future__ import annotations

from pathlib import Path

from prin.core import StringWriter
from prin.prin import main as prin_main


def _write(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _count_opening_xml_tags(text: str) -> int:
    return sum(
        1
        for line in text.splitlines()
        if line.startswith("<") and not line.startswith("</") and not line.endswith("/>")
    )


def test_max_files_limits_printed_files_all_included(tmp_path: Path):
    # Build a small tree with 5 printable files
    _write(tmp_path / "a.py", "print('a')\n")
    _write(tmp_path / "b.py", "print('b')\n")
    _write(tmp_path / "dir" / "c.py", "print('c')\n")
    _write(tmp_path / "dir" / "d.py", "print('d')\n")
    _write(tmp_path / "dir" / "sub" / "e.py", "print('e')\n")

    buf = StringWriter()
    prin_main(argv=["--max-files", "4", str(tmp_path)], writer=buf)
    out = buf.text()
    assert _count_opening_xml_tags(out) == 4


def test_max_files_skips_non_matching_and_still_prints_four(tmp_path: Path):
    # 4 printable files and one .lock that should not match by default extensions
    _write(tmp_path / "a.lock", "dummy\n")  # ensure it sorts early among files
    _write(tmp_path / "a.py", "print('a')\n")
    _write(tmp_path / "dir" / "b.py", "print('b')\n")
    _write(tmp_path / "dir" / "c.py", "print('c')\n")
    _write(tmp_path / "dir" / "sub" / "d.py", "print('d')\n")

    buf = StringWriter()
    prin_main(argv=["--max-files", "4", str(tmp_path)], writer=buf)
    out = buf.text()
    assert _count_opening_xml_tags(out) == 4

