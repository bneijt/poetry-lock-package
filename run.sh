#!/bin/bash
set -e
cd "$(dirname "$0")"
poetry run poetry-lock-package --help
poetry run poetry-lock-package --ignore 'imm..ables' --ignore 'contextvars' --no-parent
cat poetry-lock-package-lock/pyproject.toml
poetry run poetry-lock-package --build --ignore 'imm..ables' --ignore 'contextvars' --no-parent