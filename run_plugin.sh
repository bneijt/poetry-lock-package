#!/bin/bash
set -e
cd "$(dirname "$0")"
poetry install
.venv/bin/poetry build
cd dist
unzip -o poetry_lock_package-0.0.1-py3-none-any.whl