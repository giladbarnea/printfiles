from __future__ import annotations

import sys

from . import print_repo, print_files


def main() -> None:
    argv = sys.argv[1:]

    # Prefer the repo implementation if the first positional looks like a GitHub URL
    if print_repo.matches(argv):
        # Delegate; print_repo will parse sys.argv and handle subpaths/flags
        print_repo.main(None)
        return

    # Fallback to filesystem implementation
    print_files.main()


if __name__ == "__main__":
    main()


