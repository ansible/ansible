#!/usr/bin/env bash

set -eux

MYTMPDIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')
trap 'rm -rf "${MYTMPDIR}"' EXIT

BUILTIN_OUTPUT="${MYTMPDIR}/builtin_output.txt"
python -m platform| tee "${BUILTIN_OUTPUT}"

VENDORED_OUTPUT="${MYTMPDIR}/vendored_output.txt"
python -m ansible.module_utils.compat_platform| tee "${VENDORED_OUTPUT}"

diff -u "${BUILTIN_OUTPUT}" "${VENDORED_OUTPUT}"

