#!/bin/bash -eux

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "${TEST}"

version="${args[1]}"

retry.py pip install tox --disable-pip-version-check

ansible-test units --color -v --tox --coverage --python "${version}"
