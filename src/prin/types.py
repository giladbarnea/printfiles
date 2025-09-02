import os
from typing import Annotated, Callable, NewType

from annotated_types import Predicate

TPath = NewType("TPath", str)


def _is_glob(path) -> bool:
    if not isinstance(path, str):
        return False
    return any(c in path for c in "*?![]")


def _is_extension(name: str) -> bool:
    return name.startswith(".") and os.path.sep not in name


TGlob = Annotated[NewType("TGlob", str), Predicate(_is_glob)]
TExtension = Annotated[NewType("TExtension", str), Predicate(_is_extension)]

TExclusion = TPath | TGlob | Callable[[TPath | TGlob], bool]
"""
TExclusion is a union of:
- TPath: A string representing a file or directory path. Matches by substring (e.g., "foo/bar" matches "foo/bar/baz").
- TGlob: A string representing a glob pattern.
- Callable[[TPath | TGlob], bool]: A function that takes a TPath or TGlob and returns a boolean.
"""
