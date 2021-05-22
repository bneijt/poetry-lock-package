#!/bin/bash
#Build the docker container and run the in_docker_test.sh script to test
set -e
cd "$(dirname "$0")"
rm -rf dist
poetry build
docker build -t poetry-lock-test .
docker run -v `pwd`:/project:ro -it poetry-lock-test $@