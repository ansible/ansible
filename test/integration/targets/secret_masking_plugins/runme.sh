#!/usr/bin/env bash

set -eux -o pipefail

# assert_masked LOG SECRETS MARKERS
#   SECRETS: newline-separated plaintext values that must NOT appear anywhere in LOG.
#   MARKERS: newline-separated fixed strings that MUST appear in LOG (the redacted egress markers).
assert_masked() {
    local log="$1" secrets="$2" markers="$3" secret marker

    while IFS= read -r secret; do
        [ -z "${secret}" ] && continue
        if grep -q -- "${secret}" "${log}"; then
            echo "FAIL: registered secret '${secret}' leaked in plaintext (${log})" >&2
            grep -n -- "${secret}" "${log}" >&2 || true
            exit 1
        fi
    done <<< "${secrets}"

    while IFS= read -r marker; do
        [ -z "${marker}" ] && continue
        if ! grep -qF -- "${marker}" "${log}"; then
            echo "FAIL: expected redacted marker not found: '${marker}' (${log})" >&2
            exit 1
        fi
    done <<< "${markers}"
}

### filter plugin ############################################################
LOG="${OUTPUT_DIR}/filter.log"
ansible-playbook filter.yml "$@" 2>&1 | tee "${LOG}"
assert_masked "${LOG}" \
    'FilterSecret1
FilterSecret2
FilterSecret3' \
    "SCN filter_register: \$REDACTED\$
SCN filter_registers: \$REDACTED\$ \$REDACTED\$ \$REDACTED\$"

### test plugin ##############################################################
LOG="${OUTPUT_DIR}/test.log"
ansible-playbook test.yml "$@" 2>&1 | tee "${LOG}"
assert_masked "${LOG}" \
    'TestSecret1
TestSecret2
TestSecret3' \
    "SCN test_register: \$REDACTED\$
SCN test_registers: \$REDACTED\$ \$REDACTED\$ \$REDACTED\$"

### lookup plugin ############################################################
LOG="${OUTPUT_DIR}/lookup.log"
ansible-playbook lookup.yml "$@" 2>&1 | tee "${LOG}"
assert_masked "${LOG}" \
    'LookupSecret1
LookupSecret2
LookupSecret3' \
    "SCN lookup_register: \$REDACTED\$
SCN lookup_registers: \$REDACTED\$ \$REDACTED\$ \$REDACTED\$"

### vars plugin ##############################################################
LOG="${OUTPUT_DIR}/vars.log"
ANSIBLE_VARS_ENABLED=vars_test \
    ansible-playbook vars.yml "$@" 2>&1 | tee "${LOG}"
assert_masked "${LOG}" \
    'VarsSecret1
VarsSecret2
VarsSecret3' \
    "SCN vars_register: \$REDACTED\$
SCN vars_registers: \$REDACTED\$ \$REDACTED\$ \$REDACTED\$"

### inventory plugin #########################################################
LOG="${OUTPUT_DIR}/inventory.log"
ANSIBLE_INVENTORY_ENABLED=inventory_test \
    ansible-playbook inventory.yml -i inventory.inventory_test.yml "$@" 2>&1 | tee "${LOG}"
assert_masked "${LOG}" \
    'InventorySecret1
InventorySecret2
InventorySecret3' \
    "SCN inventory_register: \$REDACTED\$
SCN inventory_registers: \$REDACTED\$ \$REDACTED\$ \$REDACTED\$"

### action plugin (runs in a forked worker) ##################################
LOG="${OUTPUT_DIR}/action.log"
ANSIBLE_DEPRECATION_WARNINGS=True \
    ansible-playbook action.yml "$@" 2>&1 | tee "${LOG}"
assert_masked "${LOG}" \
    'ActionSecret1
ActionSecret2
ActionSecret3
MaskCheckActionSecret' \
    "SCN action_register: \$REDACTED\$
SCN action_registers: \$REDACTED\$ \$REDACTED\$ \$REDACTED\$
SCN action_warning: \$REDACTED\$
SCN action_deprecated: \$REDACTED\$
SCN action_persist: ok"

### connection plugin (runs in a forked worker) #############################
LOG="${OUTPUT_DIR}/connection.log"
ANSIBLE_DEPRECATION_WARNINGS=True \
    ansible-playbook connection.yml -e ansible_connection=connection_test "$@" 2>&1 | tee "${LOG}"
assert_masked "${LOG}" \
    'ConnectionSecret1
ConnectionSecret2
ConnectionSecret3
MaskCheckConnectionSecret' \
    "SCN connection_register: \$REDACTED\$
SCN connection_registers: \$REDACTED\$ \$REDACTED\$ \$REDACTED\$
SCN connection_warning: \$REDACTED\$
SCN connection_deprecated: \$REDACTED\$
SCN connection_persist: ok"

echo "All secret masking plugin registration scenarios passed."
