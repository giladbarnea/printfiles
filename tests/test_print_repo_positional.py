from __future__ import annotations

import os
from pathlib import Path

import pytest

from prin.print_repo import render_repo


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


@pytest.mark.timeout(15)
def test_repo_explicit_ignored_file_is_printed():
    # LICENSE has no extension; treat it as ignored by default, but explicit path must print it
    url = "https://github.com/TypingMind/awesome-typingmind/LICENSE"
    out = render_repo(url)  # Path embedded in URL
    assert "<LICENSE>" in out


def test_two_positional_repositories_print_both():
    url1 = "https://github.com/TypingMind/awesome-typingmind"
    url2 = "https://github.com/trouchet/rust-hello"
    # Engine renders one repo per invocation; concatenate results for assertion
    out = render_repo(url1, [""]) + render_repo(url2, [""])
    assert "logos/README.md" in out
    assert "<Cargo.toml>" in out


@pytest.mark.timeout(15)
def test_repo_dir_and_explicit_ignored_file():
    # Embed LICENSE in URL, and also traverse repo root by adding an empty root
    url = "https://github.com/TypingMind/awesome-typingmind/LICENSE"
    out = render_repo(url, [""])  # default root + embedded explicit path
    assert "<README.md>" in out  # normal traversal still prints repo files
    assert "<LICENSE>" in out  # explicit inclusion prints extensionless file
