#!/usr/bin/env bash

set -eux -o pipefail

LOG="${OUTPUT_DIR}/config_secret.log"

ANSIBLE_CONFIG=config_secret.cfg \
ANSIBLE_SECRET_PROBE_ENV="Configenv0020Secret" \
    ansible-playbook config_secret.yml -i localhost, "$@" 2>&1 | tee "${LOG}"

registered_secrets=(
    Configenv0020Secret
    Configini0021Secret
    Configvars0022Secret
    Configstring0024Secret
    Configlist0023Secret
)
for secret in "${registered_secrets[@]}"; do
    if grep -q -- "${secret}" "${LOG}"; then
        echo "FAIL: registered secret '${secret}' leaked in plaintext" >&2
        exit 1
    fi
done

markers=(
    "SCN config_env: \$REDACTED\$"
    "SCN config_ini: \$REDACTED\$"
    "SCN config_vars: \$REDACTED\$"
    "SCN config_string: \$REDACTED\$"
    "SCN config_list: \$REDACTED\$,12345678"  # Int values are not registered
)
for marker in "${markers[@]}"; do
    if ! grep -qF -- "${marker}" "${LOG}"; then
        echo "FAIL: expected redacted marker not found: '${marker}'" >&2
        exit 1
    fi
done

echo "All secret masking config secret scenarios passed."
