from __future__ import annotations

import sys

from . import print_files, print_repo


def _find_github_url(argv: list[str]) -> tuple[int, str] | None:
    patterns = (
        "https://github.com/",
        "http://github.com/",
        "git+https://github.com/",
    )
    for i, tok in enumerate(argv):
        if tok.startswith("-"):
            continue
        low = tok.strip().lower()
        if any(low.startswith(p) for p in patterns):
            return i, tok
    return None


def main() -> None:
    argv = sys.argv[1:]

    # Prefer the repo implementation if any positional arg looks like a GitHub URL
    gh = _find_github_url(argv)
    if gh is not None:
        idx, url = gh
        # Remove the URL token so repo.main(url) treats remaining positionals as subpaths
        filtered = [tok for i, tok in enumerate(argv) if i != idx]
        sys.argv = [sys.argv[0], *filtered]
        print_repo.main(url)
        return

    # Fallback to filesystem implementation
    print_files.main()


if __name__ == "__main__":
    main()
