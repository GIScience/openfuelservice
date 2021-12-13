#! /usr/bin/env bash
set -e

python /app/app/tests_pre_start.py

tox -e lint
#tox -e py39 "$@"
