#!/usr/bin/env bash

set -eux -o pipefail

SECRET=Callbacksecret0060Value

MASKED_OUT="${OUTPUT_DIR}/masked.jsonl"
RAW_OUT="${OUTPUT_DIR}/raw.jsonl"

export ANSIBLE_CALLBACK_PLUGINS="${PWD}/callback_plugins"
export ANSIBLE_STDOUT_CALLBACK=masking_probe

# Test that when callback plugins opt in to secret masking, the raw secret is still available to them.
MASKING_PROBE_OUTPUT="${RAW_OUT}" MASKING_PROBE_SUPPORTS_MASKING=1 ansible-playbook test.yml "$@"
echo "Callback output written to ${RAW_OUT}"
cat "${RAW_OUT}"

if ! grep -q -- "${SECRET}" "${RAW_OUT}"; then
    echo "FAIL: opted-in callback did not receive the raw secret; the default-path test proves nothing" >&2
    cat "${RAW_OUT}" >&2
    exit 1
fi

# Test that when callback plugins do not opt in to secret masking, the raw secret is not available to them.
MASKING_PROBE_OUTPUT="${MASKED_OUT}" ansible-playbook test.yml "$@"

echo "Callback output written to ${MASKED_OUT}"
cat "${MASKED_OUT}"

if grep -q -- "${SECRET}" "${MASKED_OUT}"; then
    echo "FAIL: secret leaked to a non-opted-in callback's serialized result" >&2
    cat "${MASKED_OUT}" >&2
    exit 1
fi
if ! grep -qF -- "\$REDACTED\$" "${MASKED_OUT}"; then
    echo "FAIL: expected redacted marker not found in non-opted-in callback output" >&2
    cat "${MASKED_OUT}" >&2
    exit 1
fi

echo "All secret masking callback scenarios passed."
