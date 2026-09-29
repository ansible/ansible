#!/usr/bin/env bash

set -eux -o pipefail

# Options passed to this script (such as -v) are ignored as they would change the output being compared.
# Disable color in output for consistency
export ANSIBLE_FORCE_COLOR=0
export ANSIBLE_NOCOLOR=1
export ANSIBLE_CALLBACKS_ENABLED=tree

rm -rf "${OUTPUT_DIR}/tree"
ANSIBLE_CALLBACK_TREE_DIR="${OUTPUT_DIR}/tree" ansible-playbook secret_masking.yml
echo >> "${OUTPUT_DIR}/tree/localhost"  # adds trailing newline so it matches git copy
cat "${OUTPUT_DIR}/tree/localhost"
diff -u secret_masking.localhost "${OUTPUT_DIR}/tree/localhost"
