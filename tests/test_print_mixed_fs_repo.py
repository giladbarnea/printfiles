import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _ensure_github_token(monkeypatch):
    """Smell: This should be moved to tests/conftest.py to ensure it runs at the beginning of the test SESSION."""
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


def test_mixed_fs_repo_interchangeably():
    """This test should pass a github URL and a mock file system root path positionally one after the other to the same main function, and assert that both are printed."""
