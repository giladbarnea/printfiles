from __future__ import annotations


class XmlFormatter:
    def header(self, path: str) -> str:
        return f"<{path}>\n</{path}>\n"

    def body(self, path: str, text: str) -> str:
        if not text.endswith("\n"):
            text = text + "\n"
        return f"<{path}>\n{text}</{path}>\n"

    def binary(self, path: str) -> str:
        return f"<{path}/>\n"


class MarkdownFormatter:
    def _sep(self, path: str) -> str:
        return "=" * (len(path) + 8)

    def header(self, path: str) -> str:
        sep = self._sep(path)
        return f"# FILE: {path}\n{sep}\n\n---\n"

    def body(self, path: str, text: str) -> str:
        sep = self._sep(path)
        return f"# FILE: {path}\n{sep}\n{text}\n\n---\n"

    def binary(self, path: str) -> str:
        return self.header(path)
