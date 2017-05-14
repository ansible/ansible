#!/bin/bash -eux

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "${TEST}"

version="${args[1]}"

retry.py pip install tox --disable-pip-version-check

# shellcheck disable=SC2086
ansible-test units --color -v --tox --python "${version}" --coverage ${CHANGED:+"$CHANGED"} \
