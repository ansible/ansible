#!/usr/bin/env bash

set -eux -o pipefail

LOG="${OUTPUT_DIR}/filter.log"

# Source file for the template-laziness scenario; the playbook edits it between uses.
LAZY_FILE="${OUTPUT_DIR}/lazy_secret_source.txt"

ansible-playbook filter.yml -i ../../inventory -e "lazy_file=${LAZY_FILE}" "$@" 2>&1 | tee "${LOG}"

# The plaintext given to the vault filter is deliberately displayed once before the filter runs, to
# prove the filter is what registers it; that line is excluded from the leak check below.
if ! grep -qF -- "MARKER vault_data_before: Vaultdata0004Secret" "${LOG}"; then
    echo "FAIL: plaintext must be visible before the vault filter registers it" >&2
    exit 1
fi
grep -vF -- "MARKER vault_data_before:" "${LOG}" > "${LOG}.after"

registered_secrets=(
    Filterregister0001Secret
    Filtermask0002Secret
    Vaultfilterpass0003Secret
    Vaultdata0004Secret
    Unvaultdata0005Secret
    Unvaultpass0006Secret
    Nondestruct0040Secret
    Lazyfirst0050Secret
    Lazysecond0051Secret
)
for secret in "${registered_secrets[@]}"; do
    if grep -q -- "${secret}" "${LOG}.after"; then
        echo "FAIL: registered secret '${secret}' leaked in plaintext" >&2
        exit 1
    fi
done

markers=(
    "MARKER filter_register: \$REDACTED\$"
    "MARKER filter_mask: \$REDACTED\$"
    "MARKER vault_filter: \$REDACTED\$"
    "MARKER vault_data: \$REDACTED\$"
    "MARKER unvault_filter: \$REDACTED\$"
    "MARKER unvault_data: \$REDACTED\$"
    "MARKER nondestruct: \$REDACTED\$"
    "MARKER lazy_use1: \$REDACTED\$"
    "MARKER lazy_first: \$REDACTED\$"
    "MARKER lazy_use2: \$REDACTED\$"
    "MARKER lazy_second: \$REDACTED\$"
)
for marker in "${markers[@]}"; do
    if ! grep -qF -- "${marker}" "${LOG}"; then
        echo "FAIL: expected redacted marker not found: '${marker}'" >&2
        exit 1
    fi
done

# A failed registration cannot mask the value, so the error output must not display the source of the template containing it.
if ! grep -qF -- "Secret must be at least 4 characters" "${LOG}"; then
    echo "FAIL: expected register_secret failure message not found" >&2
    exit 1
fi
if grep -q -- "Zq1" "${LOG}"; then
    echo "FAIL: value of a failed register_secret template was displayed" >&2
    exit 1
fi

# The same check for a registration failure raised while templating a play keyword rather than by a task.
PLAY_KEYWORD_LOG="${OUTPUT_DIR}/filter_play_keyword.log"

if ansible-playbook filter_play_keyword.yml -i ../../inventory "$@" 2>&1 | tee "${PLAY_KEYWORD_LOG}"; then
    echo "FAIL: play with a failed register_secret in a play keyword should have failed" >&2
    exit 1
fi
if ! grep -qF -- "Secret must be at least 4 characters" "${PLAY_KEYWORD_LOG}"; then
    echo "FAIL: expected register_secret failure message not found in play keyword output" >&2
    exit 1
fi
if grep -q -- "Zq2" "${PLAY_KEYWORD_LOG}"; then
    echo "FAIL: value of a failed register_secret template in a play keyword was displayed" >&2
    exit 1
fi

echo "All secret masking filter scenarios passed."
