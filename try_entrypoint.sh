#!/bin/bash
#Test run of the non-plugin entrypoint usage
set -e
cd "$(dirname "$0")"
poetry run poetry-lock-package build-lock --help
poetry run poetry-lock-package build-lock
unzip -p dist/poetry_lock_package_lock-0.0.1-py3-none-any.whl poetry_lock_package_lock-0.0.1.dist-info/METADATA

poetry run poetry-lock-package build-lock --ignore 'poetry' --no-root
unzip -p dist/poetry_lock_package_lock-0.0.1-py3-none-any.whl poetry_lock_package_lock-0.0.1.dist-info/METADATA
