### Core invariants
- Engine owns traversal/filters/printing; adapters only list/read/is_empty.
- Explicit file roots must print regardless of filters (engine handles by treating file roots as force-include).
- Paths are printed relative to each provided root (single file root prints just its basename).

### Adapters
- File system: `is_empty` via AST; raises NotADirectoryError for files (implicit via scandir).
- GitHub: list via Contents API; for file paths, raise NotADirectoryError so engine force-includes; ignore local .gitignore for repos.

### CLI and flags
- One shared parser in `cli_common` used by both implementations; no interactive prompts; consistent flags (`-t`, `-x`, `--no-ignore`, `-E`, `-l`, etc.).
- `prin` dispatches: GitHub URL → repo implementation; otherwise filesystem. Keep URL detection minimal and robust.

### Filtering semantics
- Extension-based includes; common extensionless files (e.g., LICENSE) won’t match by default—must be passed explicitly or add default patterns deliberately.
- Exclusions use the `print_files.py` substring/glob rules (not full gitignore semantics) for parity.

### Testing and rate limits
- Use tmp_path-based tests for FS; minimize GitHub API calls in repo tests; avoid reruns; prefer single small public repo (we used TypingMind/awesome-typingmind).

### uv usage
- Develop and test with: `uv sync`, `uv run pytest [helpful flags to your liking]`.
- Tooling: `uv tool install . --reinstall` (and `uv tool install git+https://github.com/giladbarnea/printfiles.git --reinstall`). This is required in order to apply code changes to the tool.

### Gotchas
- Don’t apply local `.gitignore` to remote repos.
- Keep adapter `is_empty` mandatory; GH version must download content to decide.
- When renaming package/project, update imports, scripts, tests, and GitHub adapter module paths consistently before running uv.