from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

import pytest


@pytest.fixture(autouse=True, scope="session")
def _ensure_github_token_session(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure GITHUB_TOKEN is set once per session to avoid rate limits.

    If the environment variable is already set, keep it. Otherwise, try to read
    a token from the user's home directory at ~/.github-token and set it.
    """
    if os.environ.get("GITHUB_TOKEN"):
        return
    token_path = Path.home() / ".github-token"
    try:
        token = token_path.read_text().strip()
    except Exception:
        token = ""
    if token:
        monkeypatch.setenv("GITHUB_TOKEN", token)


@pytest.fixture(scope="session")
def comprehensive_fs(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Create a reusable comprehensive filesystem tree for tests.

    This includes a small source tree, docs, configuration files, default-ignored
    categories (tests/, binary-like, lock files), and a nested package dir.
    The directory is created once per test session and can be copied or used as
    a read-only source for individual tests that need a rich layout.
    """
    base = tmp_path_factory.mktemp("comprehensive_fs")

    # Directories
    (base / "src" / "pkg").mkdir(parents=True)
    (base / "docs").mkdir()
    (base / "tests").mkdir()
    (base / "build").mkdir()
    (base / "__pycache__").mkdir(exist_ok=True)

    # Included-by-default examples
    (base / "src" / "main.py").write_text("print('hello')\nprint('world')\n", encoding="utf-8")
    (base / "docs" / "readme.md").write_text("# Title\n\nSome docs.\n", encoding="utf-8")
    (base / "src" / "config.json").write_text('{\n  "a": 1,\n  "b": 2\n}\n', encoding="utf-8")

    # Nested level
    (base / "src" / "pkg" / "module.py").write_text(
        "def f():\n    return 1\n\nprint(f())\n", encoding="utf-8"
    )
    (base / "src" / "pkg" / "data.jsonl").write_text('{"x":1}\n{"x":2}\n', encoding="utf-8")

    # Default-ignored categories (lock/test/binary)
    (base / "poetry.lock").write_text("dummy\n", encoding="utf-8")
    (base / "package-lock.json").write_text("{}\n", encoding="utf-8")
    (base / "build" / "artifact.o").touch()
    (base / "__pycache__" / "module.pyc").touch()
    (base / "tests" / "test_something.py").write_text(
        "def test_x():\n    assert True\n", encoding="utf-8"
    )

    yield base

