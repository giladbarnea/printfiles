#!/usr/bin/env bash

set -e
set -x

# mypy app
uv run ruff check . --unsafe-fixes --preview
uv run ruff format . --check --preview
