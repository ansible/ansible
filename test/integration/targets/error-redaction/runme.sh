#!/usr/bin/env bash

set -eux -o pipefail

export ANSIBLE_ROLES_PATH=../
export ANSIBLE_DEPRECATION_WARNINGS=true

REDACTION_ENABLED=0 ansible-playbook tests.yml "${@}" 2>&1 | tee "$OUTPUT_DIR/redaction-disabled.log"
REDACTION_ENABLED=1 ansible-playbook tests.yml "${@}" 2>&1 | tee "$OUTPUT_DIR/redaction-enabled.log"

redacted_count=6
unredacted_count=6

for num in $(seq 1 $redacted_count); do
    grep "REDACT_ME_$num" "$OUTPUT_DIR/redaction-disabled.log"
    grep "REDACT_ME_$num" "$OUTPUT_DIR/redaction-enabled.log" && exit 1
done

for num in $(seq 1 $unredacted_count); do
    grep "NOT_REDACTED_$num" "$OUTPUT_DIR/redaction-disabled.log"
    grep "NOT_REDACTED_$num" "$OUTPUT_DIR/redaction-enabled.log"
done

echo PASS
