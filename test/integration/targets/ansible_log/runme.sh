#!/usr/bin/env bash

set -eux

ALOG=${OUTPUT_DIR}/ansilbe_log_test.log

ansible-playbook logit.yml
[ ! -f "${ALOG}" ]

ANSIBLE_LOG_PATH=${ALOG} ansible-playbook logit.yml
[ -f "${ALOG}" ]
grep -q 'ping' "${ALOG}"
