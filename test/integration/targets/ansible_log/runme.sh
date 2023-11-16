#!/usr/bin/env bash

set -eux

ALOG=${OUTPUT_DIR}/test.log

ansible-playbook logit.yml
[ ! "$(grep -q 'ping' \"${ALOG}\")" ]

ANSIBLE_LOG_PATH=${ALOG} ansible-playbook logit.yml
grep -q 'ping' "${ALOG}"
