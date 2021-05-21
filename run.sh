#!/bin/bash
set -e
cd "$(dirname "$0")"
poetry run poetry-lock-package lock --help
poetry run poetry-lock-package lock --ignore 'imm..ables' --ignore 'contextvars' --no-root
cat poetry-lock-package-lock/pyproject.toml
poetry run poetry-lock-package lock --build --ignore 'imm..ables' --ignore 'contextvars' --no-root
