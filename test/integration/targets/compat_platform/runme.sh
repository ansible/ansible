#!/usr/bin/env bash

set -euvx

MYTMPDIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')
trap 'rm -rf "${MYTMPDIR}"' EXIT

env|sort

python -m platform
BUILTIN_OUTPUT="${MYTMPDIR}/builtin_output.txt"
BUILTIN_PLATFORM_OUTPUT=$(python -m platform| tee "${BUILTIN_OUTPUT}")
echo "${BUILTIN_PLATFORM_OUTPUT}"

python -m ansible.module_utils.compat_platform
VENDORED_OUTPUT="${MYTMPDIR}/vendored_output.txt"
VENDORED_PLATFORM_OUTPUT=$(python -m ansible.module_utils.compat_platform| tee "${VENDORED_OUTPUT}")
echo "${VENDORED_PLATFORM_OUTPUT}"

echo "diff -u of builtin and vendored"
diff -u "${BUILTIN_OUTPUT}" "${VENDORED_OUTPUT}"

# reading/writing to/from stdin/stdin  (See https://github.com/ansible/ansible/issues/23567)
# ansible-vault encrypt "$@" --vault-password-file "${VAULT_PASSWORD_FILE}" --output="${TEST_FILE_OUTPUT}" < "${TEST_FILE}"
# OUTPUT=$(ansible-vault decrypt "$@" --vault-password-file "${VAULT_PASSWORD_FILE}" --output=- < "${TEST_FILE_OUTPUT}")
# echo "${OUTPUT}" | grep 'This is a test file'

#OUTPUT_DASH=$(ansible-vault decrypt "$@" --vault-password-file "${VAULT_PASSWORD_FILE}" --output=- "${TEST_FILE_OUTPUT}")
# echo "${OUTPUT_DASH}" | grep 'This is a test file'

