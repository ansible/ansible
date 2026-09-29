#!/usr/bin/env bash

set -eux -o pipefail

# Options passed to this script (such as -v) are ignored as they would change the output being compared.
# Disable color in output for consistency
export ANSIBLE_FORCE_COLOR=0
export ANSIBLE_NOCOLOR=1
export ANSIBLE_CALLBACKS_ENABLED=junit

rm -rf "${OUTPUT_DIR}/junit"
JUNIT_OUTPUT_DIR="${OUTPUT_DIR}/junit" JUNIT_TASK_RELATIVE_PATH="${PWD}" ansible-playbook secret_masking.yml

# Normalize the filename and time attributes in the JUnit XML output for consistent comparison
sed -E 's/ time="[0-9.]+"/ time="0"/g' "${OUTPUT_DIR}"/junit/secret_masking-*.xml | tee "${OUTPUT_DIR}/secret_masking.xml"
diff -u secret_masking.xml "${OUTPUT_DIR}/secret_masking.xml"
