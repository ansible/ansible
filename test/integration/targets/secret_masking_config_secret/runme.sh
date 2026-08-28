#!/usr/bin/env bash

set -eux -o pipefail

LOG="${OUTPUT_DIR}/config_secret.log"

ANSIBLE_CONFIG=config_secret.cfg \
ANSIBLE_SECRET_PROBE_ENV="Configenv0020Secret" \
    ansible-playbook config_secret.yml "$@" 2>&1 | tee "${LOG}"

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
    "MARKER config_env: \$REDACTED\$"
    "MARKER config_ini: \$REDACTED\$"
    "MARKER config_vars: \$REDACTED\$"
    "MARKER config_string: \$REDACTED\$"
    "MARKER config_list: \$REDACTED\$,12345678"  # Int values are not registered
)
for marker in "${markers[@]}"; do
    if ! grep -qF -- "${marker}" "${LOG}"; then
        echo "FAIL: expected redacted marker not found: '${marker}'" >&2
        exit 1
    fi
done

# A plugin that marks a non-string option (type: int) as secret is invalid and must be
# rejected when its config definitions are loaded, rather than silently ignored.
BAD_LOG="${OUTPUT_DIR}/bad_config_secret.log"
if ansible-playbook bad_config_secret.yml "$@" 2>&1 | tee "${BAD_LOG}"; then
    echo "FAIL: invalid 'secret' + int config option was not rejected" >&2
    exit 1
fi
if ! grep -qF -- "cannot enable 'secret' with type 'int'" "${BAD_LOG}"; then
    echo "FAIL: expected secret/type validation error not found" >&2
    exit 1
fi

echo "All secret masking config secret scenarios passed."
