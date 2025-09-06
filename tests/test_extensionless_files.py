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


def test_extensionless_files_included_by_default(tmp_path: Path):
    _write(tmp_path / "LICENSE", "All rights reserved\n")
    _write(tmp_path / "Dockerfile", "FROM scratch\n")
    _write(tmp_path / "a.py", "print(1)\n")

    buf = StringWriter()
    prin_main(argv=["--include-tests", str(tmp_path)], writer=buf)
    out = buf.text()

    assert "<LICENSE>" in out
    assert "<Dockerfile>" in out
    assert "<a.py>" in out


def test_extensionless_respected_by_exclude_glob(tmp_path: Path):
    _write(tmp_path / "LICENSE", "All rights reserved\n")
    _write(tmp_path / "Dockerfile", "FROM scratch\n")
    _write(tmp_path / "a.py", "print(1)\n")

    buf = StringWriter()
    prin_main(argv=["--include-tests", "-E", "LICENS*", str(tmp_path)], writer=buf)
    out = buf.text()

    assert "<LICENSE>" not in out
    # Another extensionless file should still be included
    assert "<Dockerfile>" in out
    assert "<a.py>" in out

