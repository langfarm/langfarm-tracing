#! /usr/bin/env bash
set -e
set -x

coverage run --source=langfarm_tracing -m pytest
coverage report --show-missing
coverage html --title "${@-coverage}"

