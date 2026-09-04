#!/usr/bin/env bash
set -eux -o pipefail

VAULT_PASSWORD_FILE=vault-password
LOG="${OUTPUT_DIR}/lookup.log"

UNVAULT_TARGET_FILE="${OUTPUT_DIR}/unvault_target.vault"

printf "Unvaultlookup0005Secret" > "${UNVAULT_TARGET_FILE}"
ansible-vault encrypt --vault-password-file "${VAULT_PASSWORD_FILE}" "${UNVAULT_TARGET_FILE}"

ansible-playbook lookup.yml -i ../../inventory \
    --vault-password-file "${VAULT_PASSWORD_FILE}" \
    -e unvault_target_file="${UNVAULT_TARGET_FILE}" \
    "$@" 2>&1 | tee "${LOG}"

registered_secrets=(
    Passwordlookup0004Secret
    Unvaultlookup0005Secret
)
for secret in "${registered_secrets[@]}"; do
    if grep -q -- "${secret}" "${LOG}"; then
        echo "FAIL: registered secret '${secret}' leaked in plaintext" >&2
        exit 1
    fi
done

markers=(
    "MARKER password_lookup: \$REDACTED\$"
    "MARKER unvault_lookup: \$REDACTED\$"
)
for marker in "${markers[@]}"; do
    if ! grep -qF -- "${marker}" "${LOG}"; then
        echo "FAIL: expected redacted marker not found: '${marker}'" >&2
        exit 1
    fi
done

echo "All secret masking lookup scenarios passed."
