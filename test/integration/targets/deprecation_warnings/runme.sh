#!/usr/bin/env bash
# Assert the deprecation messages reported to users.

set -eux -o pipefail

export ANSIBLE_DEPRECATION_WARNINGS=True
export ANSIBLE_FORCE_COLOR=0

export ANSIBLE_INVENTORY_PLUGINS=./inventory_plugins
ansible-inventory --list -i inventories/invalid_var_names.yml 2>&1 | tee out.txt
grep out.txt -e "\[DEPRECATION WARNING\]: Accepting inventory variable with invalid name 'var-"
grep out.txt -e "\[DEPRECATION WARNING\]: Accepting inventory variable with invalid name 'group-"

ansible-playbook args_empty.yml 2>&1 | tee out.txt
tr -s '[:space:]' ' ' < out.txt > out_unwrapped.txt
grep out_unwrapped.txt -e "\[DEPRECATION WARNING\]: Ignoring empty task \`args\` keyword."
grep out_unwrapped.txt -e "\[DEPRECATION WARNING\]: Merging legacy k=v args ('kv1') into task args."
grep out_unwrapped.txt -e "\[DEPRECATION WARNING\]: Using a mapping for \`action\` is deprecated."

ansible-playbook to_bool.yml 2>&1 | tee out.txt
tr -s '[:space:]' ' ' < out.txt > out_unwrapped.txt
grep out_unwrapped.txt -e "\[DEPRECATION WARNING\]: The \`bool\` filter coerced invalid value None (NoneType) to False"
grep out_unwrapped.txt -e "\[DEPRECATION WARNING\]: The \`bool\` filter coerced invalid value 1.0 (float) to True"
grep out_unwrapped.txt -e "\[DEPRECATION WARNING\]: The \`bool\` filter coerced invalid value 0.0 (float) to False"
grep out_unwrapped.txt -e "\[DEPRECATION WARNING\]: The \`bool\` filter coerced invalid value 7 (int) to False"
grep out_unwrapped.txt -e "\[DEPRECATION WARNING\]: The \`bool\` filter coerced invalid value {} (dict) to False"

ansible-playbook from_yaml.yml 2>&1 | tee out.txt
grep out.txt -e "\[DEPRECATION WARNING\]: The from_yaml_all filter ignored non-string"
grep out.txt -e "\[DEPRECATION WARNING\]: The from_yaml filter ignored non-string"

ansible-playbook non_boolean_test_plugins.yml 2>&1 | tee out.txt
grep out.txt -e "\[DEPRECATION WARNING\]: The test plugin 'passthru' returned a non-boolean result"
# the warning text is wrapped to the terminal width, so unwrap it before matching the full message
tr -s '[:space:]' ' ' < out.txt > out_unwrapped.txt
grep out_unwrapped.txt -e "The test plugin 'passthru' returned a non-boolean result of type <class 'str'>"
grep out_unwrapped.txt -e "The test plugin 'passthru' returned a non-boolean result of type <class 'int'>"

ANSIBLE_ALLOW_BROKEN_CONDITIONALS=1 ansible-playbook empty_conditional.yml 2>&1 | tee out.txt
grep out.txt -e "\[DEPRECATION WARNING\]: Empty conditional expression was evaluated as True."
ANSIBLE_ALLOW_BROKEN_CONDITIONALS=0 ansible-playbook empty_conditional.yml 2>&1 | tee out.txt
grep out.txt -e "Empty conditional expressions are not allowed."
