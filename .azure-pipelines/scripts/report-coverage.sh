#!/usr/bin/env bash
# Generate code coverage reports for uploading to Azure Pipelines and codecov.io.

set -o pipefail -eu

PATH="${PWD}/bin:${PATH}"

ansible-test coverage xml --stub --venv --venv-system-site-packages --color -v
