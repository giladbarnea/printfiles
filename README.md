### prin

Engine-driven depth-first traversal with source adapters; the engine is source-agnostic while implementations (filesystem, GitHub) provide listing/reading. Shared filters/formatters ensure identical behavior across sources.

### Development
- Setup and test: `uv sync`; `uv run python -m pytest -q`
- Install locally as a tool: `uv tool install .`
- Install remotely as a tool: `uv tool install git+https://github.com/giladbarnea/printfiles.git`