#!/usr/bin/env bash

set -eux -o pipefail

VAULT_PASSWORD_FILE=vault-password
LOG="${OUTPUT_DIR}/vault.log"

VAULTED_VARS_FILE="${OUTPUT_DIR}/vaulted_vars.yml"
INLINE_VAULT_FILE="${OUTPUT_DIR}/inline_vault_vars.yml"

cp vars/vaulted_source.yml "${VAULTED_VARS_FILE}"
ansible-vault encrypt --vault-password-file "${VAULT_PASSWORD_FILE}" "${VAULTED_VARS_FILE}"

ansible-vault encrypt_string --vault-password-file "${VAULT_PASSWORD_FILE}" \
    --name inline_vault_secret "Vaultinline0013Secret" > "${INLINE_VAULT_FILE}"

ansible-playbook vault.yml -i ../../inventory \
    --vault-password-file "${VAULT_PASSWORD_FILE}" \
    -e vaulted_vars_file="${VAULTED_VARS_FILE}" \
    -e inline_vault_file="${INLINE_VAULT_FILE}" \
    "$@" 2>&1 | tee "${LOG}"

registered_secrets=(
    Vaultfilescalar0010Secret
    Vaultfilelist0011Secret
    Vaultfiledict0012Secret
    Vaultfilekeyval0014Secret
    Vaultinline0013Secret
    Vaultdictinlist0015Secret
    Vaultlistindict0016Secret
    Vaultdeep0017Secret
    87654321
)
for secret in "${registered_secrets[@]}"; do
    if grep -q -- "${secret}" "${LOG}"; then
        echo "FAIL: registered secret '${secret}' leaked in plaintext" >&2
        exit 1
    fi
done

markers=(
    "MARKER vault_scalar: \$REDACTED\$"
    "MARKER vault_list: \$REDACTED\$"
    "MARKER vault_dict: \$REDACTED\$"
    "MARKER vault_int: \$REDACTED\$"
    "MARKER vault_inline: \$REDACTED\$"
    "MARKER vault_dict_in_list: \$REDACTED\$"
    "MARKER vault_list_in_dict: \$REDACTED\$"
    "MARKER vault_deep: \$REDACTED\$"
)
for marker in "${markers[@]}"; do
    if ! grep -qF -- "${marker}" "${LOG}"; then
        echo "FAIL: expected redacted marker not found: '${marker}'" >&2
        exit 1
    fi
done

# the value is masked but its key name is never registered
grep -qF -- "MARKER vault_keyval: key=notasecretkeyname value=\$REDACTED\$" "${LOG}"

echo "All secret masking vault scenarios passed."
