#!/usr/bin/env bash

set -eux -o pipefail

# Options passed to this script (such as -v) are ignored as they would change the output being compared.
# Disable color in output for consistency
export ANSIBLE_FORCE_COLOR=0
export ANSIBLE_NOCOLOR=1
export ANSIBLE_STDOUT_CALLBACK=oneline

ansible-playbook secret_masking.yml | tee "${OUTPUT_DIR}/secret_masking.stdout"
diff -u secret_masking.stdout "${OUTPUT_DIR}/secret_masking.stdout"
