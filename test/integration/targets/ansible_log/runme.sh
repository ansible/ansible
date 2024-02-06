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
ANSIBLE_LOG_PATH=${ALOG} ANSIBLE_LOG_VERBOSITY=3 ansible-playbook -v logit.yml | tee /dev/stderr | (! grep EXEC)
grep -q EXEC "${ALOG}"
