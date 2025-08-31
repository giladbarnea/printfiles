#!/usr/bin/env bash

set -e
set -x

# mypy app
uv run ruff check .
uv run ruff format . --check
