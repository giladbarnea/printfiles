### prin

Engine-driven depth-first traversal with source adapters; the engine is source-agnostic while implementations (filesystem, GitHub) provide listing/reading. Shared filters/formatters ensure identical behavior across sources.

### Development
- Setup and test: `uv sync`; `uv run python -m pytest -q`
- Install locally as a tool: `uv tool install .`
- Install remotely as a tool: `uv tool install git+https://github.com/giladbarnea/printfiles.git`

Options Roadmap

-H, --hidden (alias: --include-hidden)
Include hidden files and directories in the search (dotfiles and dot-directories).

-I, --no-ignore (re-enable with --ignore)
Disable all ignore rules (e.g., from .gitignore, .ignore, .fdignore, and global ignore files).

--no-ignore-vcs (alias: --ignore-gitignore; re-enable with --ignore-vcs)
Do not respect Version Control System (VCS) ignore rules (such as .gitignore, .git/info/exclude, and global gitignore).

--ignore-file <path>
Add an additional ignore-file in .gitignore format (lower precedence than command-line excludes).

-E, --exclude <glob or regex> (repeatable; alias: --ignore <glob>)
Exclude files or directories by shell-style glob or regex (identified automatically). Repeat to add multiple patterns (e.g., --exclude '*.log').

-g, --glob, --force-glob
Force the interpretation of the search pattern as a glob (instead of a regular expression).
Examples: prin -g '*.py', prin -g 'src/**/test_*.rs'.

-e, --extension <ext> (repeatable)
Only include files with the given extension (e.g., -e rs -e toml).

-S, --size <constraint>
Filter by file size. Format: <+|-><NUM><UNIT> (e.g., +10k, -2M, 500b). Units: b, k, m, g, t, ki, mi, gi, ti.

-s, --case-sensitive
Force case-sensitive matching of the search pattern. By default, case sensitivity is "smart".

-i, --ignore-case
Force case-insensitive matching of the search pattern. By default, case sensitivity is "smart".

-H, --hidden (listed above for clarity)

-u, --unrestricted
Unrestricted search: include hidden files and disable ignore rules (equivalent to --hidden --no-ignore).

-uu
Equivalent to --no-ignore --hidden.

-uuu
Equivalent to --no-ignore --hidden --binary.

-L, --follow
Follow symbolic links.

-d, --max-depth <n>
Limit directory traversal to at most <n> levels.

-A, --absolute-paths
Print absolute paths (instead of paths relative to the current working directory).

-a, --text
Treat binary files as text (search and print them as-is).

-n, --line-number (alias: --line-numbers)
Show line numbers in printed file contents.