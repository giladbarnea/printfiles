# Agents.md

Read all Markdown files in the root dir of this project before reading this file.

### Architecture

Engine-driven depth-first traversal with source adapters; the engine is source-agnostic while implementations (filesystem, GitHub) provide listing/reading. Shared filters/formatters ensure identical behavior across sources.

### Core invariants
- Engine owns traversal/filters/printing; adapters only list/read/is_empty.
- Explicit file paths must print regardless of filters (engine handles by treating file paths as force-include).
- Paths are printed relative to each provided root (single file path prints just its basename).
- print_files.py and print_repo.py should behave exactly the same way: same CLI, same filters, same output. For the user, they should be interchangeable. Internally, they should leverage as much shared code as possible.

### Adapters
- File system: `is_empty` via AST; raises NotADirectoryError for files (implicit via scandir).
- GitHub: list via Contents API; for file paths, raise NotADirectoryError so engine force-includes; ignore local .gitignore for repos.

### CLI and flags
- One shared parser in `cli_common` used by both implementations; no interactive prompts; consistent flags (`-e`, `-E`, `--no-ignore`, `-l`, etc.).
- `prin` dispatches: GitHub URL → repo implementation; otherwise filesystem. Keep URL detection minimal and robust.

### Filtering semantics
- Extension-based includes; common extensionless files (e.g., LICENSE) won’t match by default—must be passed explicitly or add default patterns deliberately.
- Exclusions use the `print_files.py` substring/glob rules (not full gitignore semantics) for parity.

### Testing and rate limits
- Use tmp_path-based tests for FS; minimize GitHub API calls in repo tests; avoid reruns; prefer single small public repo (we use TypingMind/awesome-typingmind and trouchet/rust-hello).

### uv usage: execution, tooling and packaging
Everything should be executed, installed, tested and packaged using uv.
- Develop and test with: `uv sync`, `uv run pytest [helpful flags to your liking]`.
- Tooling: `uv tool install . --reinstall` (and `uv tool install git+https://github.com/giladbarnea/prin.git --reinstall`). Reinstalling is required to apply code changes to the tool.

### Gotchas
- Don’t apply local `.gitignore` to remote repos. It is illogical: by definition, nothing in .gitignore will match remote files.

## Being an Effective AI Agent

1. You do your best work when you have a way to check it. Probe for one if none is explicitly provided. Verification enables continuous trial and error instead of a single shot in the dark. When testing, run both problem-specific tests and wider tests to discover potential regression problems. Trial & error loop goes like this: Give me clear and succinct status update; tell me your planned changes; apply them; run tests; repeat.
2. Know your weaknesses: your eagerness to solve a problem can lead to tunnel vision. You may fix the issue but unintentionally create code duplication, deviate from the existing design, or introduce a regression in other coupled parts of the project you didn’t consider. The solution is to often literally look around beyond the immediate problem, be aware of (and account for) coupling around the codebase, try to integrate with the existing design, and periodically refactor.