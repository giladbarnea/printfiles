from __future__ import annotations

from typing import Iterable

GITHUB_URL_PATTERNS: tuple[str, ...] = (
    "https://github.com/",
    "http://github.com/",
    "git+https://github.com/",
)


def is_github_url(token: str) -> bool:
    tok = token.strip().lower()
    if tok.startswith("-"):
        return False
    return any(tok.startswith(p) for p in GITHUB_URL_PATTERNS)


def find_github_url(argv: Iterable[str]) -> tuple[int, str] | None:
    for i, tok in enumerate(argv):
        if is_github_url(tok):
            return i, tok
    return None
