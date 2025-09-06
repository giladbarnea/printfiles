from __future__ import annotations

import os
from pathlib import Path

import pytest

from prin.core import StringWriter
from prin.prin import main as prin_main


@pytest.fixture(autouse=True)
def _ensure_github_token(monkeypatch):
    # If not set, try to load from ~/.github-token to avoid rate limits
    if os.environ.get("GITHUB_TOKEN"):
        return
    token_path = Path.home() / ".github-token"
    try:
        token = token_path.read_text().strip()
    except Exception:
        token = ""
    if token:
        monkeypatch.setenv("GITHUB_TOKEN", token)


def _count_md_headers(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.startswith("# FILE: "))


def test_repo_max_files_one():
    url = "https://github.com/TypingMind/awesome-typingmind"
    buf = StringWriter()
    prin_main(argv=[url, "--max-files", "1", "--tag", "md"], writer=buf)
    out = buf.text()
    assert _count_md_headers(out) == 1

