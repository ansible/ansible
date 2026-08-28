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


# Test the built-in callbacks which opt in to ANSIBLE_SUPPORTS_MASKING and are responsible for masking their own output.
assert_masked() {
    local log="$1"

    if grep -q -- "${SECRET}" "${log}"; then
        echo "FAIL: registered secret leaked in plaintext (${log})" >&2
        grep -n -- "${SECRET}" "${log}" >&2 || true
        exit 1
    fi
    if ! grep -qF -- "\$REDACTED\$" "${log}"; then
        echo "FAIL: expected redacted marker not found (${log})" >&2
        exit 1
    fi
}

for stdout_callback in default minimal oneline; do
    LOG="${OUTPUT_DIR}/${stdout_callback}.log"
    ANSIBLE_STDOUT_CALLBACK="${stdout_callback}" ansible-playbook test.yml -v "$@" 2>&1 | tee "${LOG}"
    assert_masked "${LOG}"
done

# junit writes a report file
JUNIT_DIR="${OUTPUT_DIR}/junit"
rm -rf "${JUNIT_DIR}"
ANSIBLE_STDOUT_CALLBACK=default ANSIBLE_CALLBACKS_ENABLED=junit JUNIT_OUTPUT_DIR="${JUNIT_DIR}" ansible-playbook test.yml "$@"
cat "${JUNIT_DIR}"/*.xml
assert_masked "$(ls "${JUNIT_DIR}"/*.xml)"

# tree writes a per host file
TREE_DIR="${OUTPUT_DIR}/tree"
rm -rf "${TREE_DIR}"
ANSIBLE_STDOUT_CALLBACK=default ANSIBLE_CALLBACKS_ENABLED=tree ANSIBLE_CALLBACK_TREE_DIR="${TREE_DIR}" ansible-playbook test.yml "$@"
cat "${TREE_DIR}/localhost"
assert_masked "${TREE_DIR}/localhost"

echo "All built-in callback secret masking scenarios passed."
