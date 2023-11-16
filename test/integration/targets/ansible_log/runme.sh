#!/usr/bin/env bash

set -eux

ALOG=${OUTPUT_DIR}/test.log

ansible-playbook logit.yml
grep -q 'ping' "${ALOG}" && /bin/false || /bin/true

ANSIBLE_LOG_PATH=${ALOG} ansible-playbook logit.yml
grep -q 'ping' "${ALOG}"
