#!/bin/bash
set -e
echo BUILD ALL
for d in */; do
(
	set -e
	echo "-> $d"
	cd "$d"
	poetry lock
	poetry install
	poetry build
	../../.venv/bin/poetry-lock-package --build
	.venv/bin/pip install dist/*_lock*.whl
)
done
