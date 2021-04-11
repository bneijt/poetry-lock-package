#!/bin/bash
cd "$(dirname "$0")"
poetry run poetry-lock-package
cat poetry-lock-package-lock/pyproject.toml