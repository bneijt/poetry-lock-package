#!/bin/bash
set -e
cd "$(dirname "$0")"
poetry run poetry-lock-package --help
poetry run poetry-lock-package --ignore 'imm..ables' --ignore 'contextvars' --no-root
cat poetry-lock-package-lock/pyproject.toml
.venv/bin/poetry run poetry-lock-package --build --ignore 'imm..ables' --ignore 'contextvars' --no-root