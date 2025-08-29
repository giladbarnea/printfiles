## Goal
Unify both scripts behind a single traversal/printing “engine”, with source-specific adapters. Let the filesystem implementation be the reference (leader), and let the GitHub repo implementation cherry-pick only what’s needed to adapt to its domain.

### Core idea
Separate three concerns:

Source adapter: knows how to enumerate a tree and read files (filesystem vs GitHub).
Engine: generic depth-first traversal, filtering, emptiness checks (when supported), and printing.
Formatter: path/content to output string (xml/md), streaming or string-building.

### Minimal interfaces

```py
# printfiles/core.py
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import PurePosixPath
from typing import Iterable, Optional, Protocol

class NodeKind(Enum):
    DIRECTORY = auto()
    FILE = auto()
    OTHER = auto()

@dataclass(frozen=True)
class Entry:
    # Always POSIX-style for cross-source consistency
    path: PurePosixPath
    name: str
    kind: NodeKind

class SourceAdapter(Protocol):
    def resolve_root(self, root_spec: str) -> PurePosixPath: ...
    def list_dir(self, dir_path: PurePosixPath) -> Iterable[Entry]: ...
    def read_file_bytes(self, file_path: PurePosixPath) -> bytes: ...
    def supports_empty_check(self) -> bool: ...
    def is_empty(self, file_path: PurePosixPath) -> bool: ...  # only if supports_empty_check()

class Formatter(Protocol):
    def header(self, path: str) -> str: ...
    def body(self, path: str, text: str) -> str: ...
    def binary(self, path: str) -> str: ...

@dataclass
class FilterConfig:
    custom_extensions: list[str]                 # e.g. ['.py', 'json*'] or glob-ish
    include_docs: bool                           # adds md/rst if True
    include_tests: bool
    include_lock: bool
    include_binary: bool
    no_ignore: bool                              # disable gitignore processing (fs-only)
    no_exclude: bool
    custom_excludes: list[str | callable]        # same semantics as print_files

@dataclass
class PrintConfig:
    only_headers: bool
    include_empty: bool
    confirm_interactive: bool

class DepthFirstPrinter:
    def __init__(self, source: SourceAdapter, formatter: Formatter,
                 filter_config: FilterConfig, print_config: PrintConfig):
        self.source = source
        self.formatter = formatter
        self.filters = filter_config
        self.prints = print_config

    def run(self, roots: list[str], write) -> None:
        # write: Callable[[str], None]  (streaming sink)
        for root_spec in roots or ["." ]:
            root = self.source.resolve_root(root_spec)
            stack = [root]
            while stack:
                current = stack.pop()
                # list_dir must yield Entry(kind=DIR/FILE/OTHER), sorted stable by name
                entries = list(self.source.list_dir(current))
                dirs = [e for e in entries if e.kind is NodeKind.DIRECTORY]
                files = [e for e in entries if e.kind is NodeKind.FILE]

                for entry in dirs:
                    if not self._excluded(entry):  # path-based filter
                        stack.append(entry.path)

                for entry in files:
                    if self._excluded(entry):
                        continue
                    if not self._extension_match(entry):
                        continue
                    if not self.prints.include_empty and self.source.supports_empty_check():
                        if self.source.is_empty(entry.path):
                            continue
                    if self.prints.only_headers:
                        write(self.formatter.header(str(entry.path)))
                        continue

                    blob = self.source.read_file_bytes(entry.path)
                    if self._is_text(blob):
                        text = self._decode_text(blob)
                        write(self.formatter.body(str(entry.path), text))
                    else:
                        if self.filters.include_binary:
                            write(self.formatter.binary(str(entry.path)))

    # _excluded, _extension_match, _is_text, _decode_text:
    # Port these from print_files.py (leader), keeping its semantics.
```
Notes:

The engine is ignorant of where files come from.
Filesystem and GitHub adapters normalize to PurePosixPath.
Emptiness filtering is delegated to the adapter. FS implements via AST (current logic). GitHub can return False unless we opt-in to fetch content (rate-limit risk).

### Concrete adapters
File system (leader), in printfiles/adapters/filesystem.py

resolve_root: resolve/canonicalize a local path.
list_dir: use os.scandir, map to Entry; sort with casefold.
read_file_bytes: read from disk.
supports_empty_check: True.
is_empty: reuse your AST-only-imports/docstring check.
Extra: expose a helper to load .gitignore/global excludes; engine merges these when no_ignore is False.
GitHub repository, in printfiles/adapters/github.py

resolve_root: parse URL and resolve default branch. Represent root as PurePosixPath("") under a context holding owner/repo/ref.
list_dir: call Contents API for a path; map dirs/files to Entry. Stable sort: directories first, then files by name (you already do this).
read_file_bytes: reuse your robust bytes retrieval (content field, download_url, blob fallback) and simple retry on rate-limit with the MAX_WAIT_SECONDS logic.
supports_empty_check: configurable; default False to avoid extra API calls. Optionally True if user explicitly enables content reads for emptiness checks.
is_empty: if enabled, fetch bytes, decode if text, run the same AST-based emptiness predicate (shared from core).

### Formatters
XML and Markdown, in printfiles/formatters.py
```py
class XmlFormatter:
    def header(self, path: str) -> str:
        return f"<{path}>\n</{path}>\n"

    def body(self, path: str, text: str) -> str:
        return f"<{path}>\n{text if text.endswith('\\n') else text + '\\n'}</{path}>\n"

    def binary(self, path: str) -> str:
        return f"<{path}/>\n"

class MarkdownFormatter:
    def header(self, path: str) -> str:
        sep = "=" * (len(path) + 8)
        return f"# FILE: {path}\n{sep}\n\n---\n"

    def body(self, path: str, text: str) -> str:
        sep = "=" * (len(path) + 8)
        return f"# FILE: {path}\n{sep}\n{text}\n\n---\n"

    def binary(self, path: str) -> str:
        return self.header(path)
```

Glue code: keep current CLIs, switch to engine
Filesystem CLI (current printfiles.print_files:main):

Parse existing flags as-is.
Build FilterConfig and PrintConfig from args.
Choose XmlFormatter or MarkdownFormatter based on --tag.
Use FileSystemSource(); call DepthFirstPrinter(...).run(paths, write=sys.stdout.write).
GitHub CLI (update print_repo.py to match flags)

Reuse the same parser options where applicable (extensions, excludes, include flags).
Add only GitHub-specific flags (token handling if needed).
Choose formatter by --tag.
Use GitHubRepoSource(session, url); call engine with roots=[""] or a path.
What moves where (from print_files.py)
Move as-is into core:
Extension resolution: resolve_extensions, default/doc extensions list.
Exclude machinery: DEFAULT_EXCLUSIONS, lock/test/binary exclude helpers, predicate formatting, is_excluded.
Text detection and decoding helpers.
Keep filesystem-only in FS adapter:
.gitignore and .git/info/exclude readers (controlled by no_ignore).
The AST-based emptiness check implementation.
Port into GitHub adapter:
Your requests session handling, rate-limit handling, content download fallbacks.
Lightweight text detection (reuse shared helpers).

### Why this works well
The engine owns traversal, filtering, and formatting “movements”.
Each adapter owns “how to see and read a tree”.
Shared filters/semantics stay consistent across both domains, led by the filesystem version.
You can stream to stdout, or accumulate in-memory for returning a single string.

### Optional refinements
Add Capability flags on adapters (e.g., can_stream_bytes, can_list_large_dirs_efficiently) if you later want engine strategies to adapt.
Provide a Writer protocol for output sinks (stdout, buffer, file, websocket).
Expose a single parse_common_args() builder so both CLIs stay in sync.

## Next steps I can implement
Create printfiles/core.py, printfiles/adapters/{filesystem,github}.py, and printfiles/formatters.py.
Refactor print_files.py and print_repo.py to the new engine.
Harmonize print_repo.py CLI to match print_files.py flags.
Keep behavior identical by default; add opt-in for GitHub emptiness checks.
If you want me to proceed, I’ll scaffold the modules, move the shared logic from print_files.py, and switch both CLIs over with tests to confirm parity.