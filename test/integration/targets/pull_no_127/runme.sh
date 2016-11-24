#!/usr/bin/env bash

set -eux
set -o pipefail

# http://unix.stackexchange.com/questions/30091/fix-or-alternative-for-mktemp-in-os-x
MYTMPDIR=$(shell mktemp -d 2>/dev/null || mktemp -d -t 'ansible-testing-XXXXXXXXXX')
trap 'rm -rf "${MYTMPDIR}"' EXIT

# test for https://github.com/ansible/ansible/issues/13681
ANSIBLE_CONFIG='' ansible-pull -d "${MYTMPDIR}" -U https://github.com/ansible-test-robinro/pull-integration-test "$@" \
    | grep -v '127\.0\.0\.1'
