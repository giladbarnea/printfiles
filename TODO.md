### Test coverage conclusion

- Untested features (from tests/ scan):
  - include/exclude tests flags: `-T/--include-tests`, `-K/--include-lock`, `-a/--text --include-binary --binary`, `-M/--include-empty`, `-l/--only-headers`, `--tag md|xml` (XML is covered indirectly; MD not explicitly).
  - parser wiring for `--exclude/--ignore` and `-e/--extension` is indirectly covered via helpers, but no end-to-end CLI invocation tests for `prin` script; coverage is via engine and helpers.
  - repo path extraction and traversal are covered; however, formatting options and include-empty/only-headers on repo path are not covered.
  - many planned options remain unimplemented; by definition they’re untested: hidden, no-ignore-vcs toggle, ignore-file, glob/force-glob, size, case-sensitive/ignore-case, unrestricted combos (`-u`/`-uu`/`-uuu`), follow symlinks, max-depth, absolute-paths, line-number.

