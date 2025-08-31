from __future__ import annotations

import pytest
from prin.adapters.github import GitHubRepoSource
from prin.core import DepthFirstPrinter
from prin.formatters import XmlFormatter
from prin.print_repo import _extract_in_repo_subpath


def _run_repo(url: str, subpaths: list[str] | None = None) -> str:
    class _Buf:
        def __init__(self) -> None:
            self.parts: list[str] = []

        def write(self, s: str) -> None:
            self.parts.append(s)

        def text(self) -> str:
            return "".join(self.parts)

    src = GitHubRepoSource(url)
    p = DepthFirstPrinter(
        src,
        XmlFormatter(),
        include_empty=True,
        only_headers=False,
        extensions=[".md", ".txt", ".py", ".json"],
        exclude=[],
    )
    buf = _Buf()
    # Derive initial root from URL if a subpath is embedded; allow explicit extra roots
    derived = _extract_in_repo_subpath(url).strip("/")
    roots: list[str] = []
    if derived:
        roots.append(derived)
    if subpaths:
        roots.extend(subpaths)
    if not roots:
        roots = [""]
    p.run(roots, buf)
    return buf.text()


@pytest.mark.timeout(15)
def test_repo_explicit_ignored_file_is_printed():
    # LICENSE has no extension; treat it as ignored by default, but explicit path must print it
    url = "https://github.com/TypingMind/awesome-typingmind/LICENSE"
    out = _run_repo(url)  # Path embedded in URL
    assert "<LICENSE>" in out


def test_two_positional_repositories_print_both():
    url1 = "https://github.com/TypingMind/awesome-typingmind"
    url2 = "https://github.com/trouchet/rust-hello"
    out = _run_repo(url1, url2, [""])
    assert "logos/README.md" in out
    assert "<Cargo.toml>" in out


@pytest.mark.timeout(15)
def test_repo_dir_and_explicit_ignored_file():
    # Embed LICENSE in URL, and also traverse repo root by adding an empty root
    url = "https://github.com/TypingMind/awesome-typingmind/LICENSE"
    out = _run_repo(url, [""])  # default root + embedded explicit path
    assert "<README.md>" in out  # normal traversal still prints repo files
    assert "<LICENSE>" in out  # explicit inclusion prints extensionless file
