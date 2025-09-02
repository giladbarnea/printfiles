from __future__ import annotations

from pathlib import Path


def write_text_file(path: Path, content: str) -> None:
    """Create parents and write UTF-8 text to a file path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def touch_file(path: Path) -> None:
    """Create parents as needed and touch a file path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()

