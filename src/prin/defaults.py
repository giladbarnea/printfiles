from prin.types import TExclusion

DEFAULT_EXCLUSIONS: list[TExclusion] = [
    lambda x: x.endswith("egg-info"),
    "build",
    "bin",
    "dist",
    "node_modules",
    lambda x: x.startswith("."),
    lambda x: "cache" in str(x).lower(),
    # Build artifacts and dependencies
    "target",
    "vendor",
    "out",
    "coverage",
    # IDE and editor files
    "*.swp",
    "*.swo",
    # Language-specific
    "*.class",
    "*.o",
    "*.so",
    "*.dylib",
    # Logs and temporary files
    "logs",
    "*.log",
    "*.tmp",
    # Environment and secrets
    "secrets",
    "*.key",
    "*.pem",
]
