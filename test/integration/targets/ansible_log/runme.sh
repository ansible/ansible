#!/usr/bin/env bash

set -eux

ALOG=${OUTPUT_DIR}/ansible_log_test.log

ansible-playbook logit.yml
[ ! -f "${ALOG}" ]

ANSIBLE_LOG_PATH=${ALOG} ansible-playbook logit.yml
[ -f "${ALOG}" ]
grep -q 'ping' "${ALOG}"

rm "${ALOG}"
# inline grep should fail if EXEC was present
set +e
ANSIBLE_LOG_PATH=${ALOG} ANSIBLE_LOG_VERBOSITY=3 ansible-playbook -v logit.yml | tee /dev/stderr | grep -q EXEC
rc=$?
set -e
if [ "$rc" == "0" ]; then
    false  # fail if we found EXEC in stdout
fi
grep -q EXEC "${ALOG}"

# Test that setting verbosity with no log won't crash
ANSIBLE_LOG_VERBOSITY=2 ansible-playbook logit.yml
