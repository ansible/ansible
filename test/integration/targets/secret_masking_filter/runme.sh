#!/usr/bin/env bash

set -eux -o pipefail

LOG="${OUTPUT_DIR}/filter.log"

ansible-playbook filter.yml -i ../../inventory "$@" 2>&1 | tee "${LOG}"

registered_secrets=(
    Filterregister0001Secret
    Filtermask0002Secret
    Vaultfilterpass0003Secret
    Nondestruct0040Secret
)
for secret in "${registered_secrets[@]}"; do
    if grep -q -- "${secret}" "${LOG}"; then
        echo "FAIL: registered secret '${secret}' leaked in plaintext" >&2
        exit 1
    fi
done

markers=(
    "SCN filter_register: \$REDACTED\$"
    "SCN filter_mask: \$REDACTED\$"
    "SCN vault_filter: \$REDACTED\$"
    "SCN nondestruct: \$REDACTED\$"
)
for marker in "${markers[@]}"; do
    if ! grep -qF -- "${marker}" "${LOG}"; then
        echo "FAIL: expected redacted marker not found: '${marker}'" >&2
        exit 1
    fi
done

echo "All secret masking filter scenarios passed."
