#!/bin/bash
set -xe
poetry --version

poetry new example-project
find
cd example-project
poetry lock
poetry plugin add /project/dist/*.whl
poetry plugin show
poetry build-lock --help
poetry build-lock

