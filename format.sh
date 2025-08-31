#!/usr/bin/env bash
set -x

uv run ruff check . --fix --preview --unsafe-fixes
uv run ruff format . --preview
