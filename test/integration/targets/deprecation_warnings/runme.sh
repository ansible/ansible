#!/usr/bin/env bash
# Assert the deprecation messages reported to users.

set -eux -o pipefail

export ANSIBLE_DEPRECATION_WARNINGS=True
# keep ANSI escapes out of the output being matched
export ANSIBLE_NOCOLOR=1
export ANSIBLE_FORCE_COLOR=0

export ANSIBLE_INVENTORY_PLUGINS=./inventory_plugins
ansible-inventory --list -i inventories/invalid_var_names.yml 2>&1 | tee out.txt
grep out.txt -e "\[DEPRECATION WARNING\]: Accepting inventory variable with invalid name 'var-"
grep out.txt -e "\[DEPRECATION WARNING\]: Accepting inventory variable with invalid name 'group-"

ansible-playbook args_empty.yml

ansible-playbook to_bool.yml

ansible-playbook from_yaml.yml 2>&1 | tee out.txt
grep out.txt -e "\[DEPRECATION WARNING\]: The from_yaml_all filter ignored non-string"
grep out.txt -e "\[DEPRECATION WARNING\]: The from_yaml filter ignored non-string"

ansible-playbook non_boolean_test_plugins.yml 2>&1 | tee out.txt
grep out.txt -e "\[DEPRECATION WARNING\]: The test plugin 'passthru' returned a non-boolean result"
# the warning text is wrapped to the terminal width, so unwrap it before matching the full message
tr -s '[:space:]' ' ' < out.txt > out_unwrapped.txt
grep out_unwrapped.txt -e "The test plugin 'passthru' returned a non-boolean result of type <class 'str'>"
grep out_unwrapped.txt -e "The test plugin 'passthru' returned a non-boolean result of type <class 'int'>"

ansible-playbook available_variables.yml 2>&1 | tee out.txt
grep out.txt -e "\[DEPRECATION WARNING\]: Direct access to the"
# the warning text is wrapped to the terminal width, so unwrap it before matching the full message
tr -s '[:space:]' ' ' < out.txt > out_unwrapped.txt
grep out_unwrapped.txt -e "Direct access to the \`_available_variables\` internal attribute is deprecated. Use \`available_variables\` instead."

ansible-playbook loader.yml 2>&1 | tee out.txt
grep out.txt -e "\[DEPRECATION WARNING\]: Direct access to the"
# the warning text is wrapped to the terminal width, so unwrap it before matching the full message
tr -s '[:space:]' ' ' < out.txt > out_unwrapped.txt
grep out_unwrapped.txt -e "Direct access to the \`_loader\` internal attribute is deprecated. Use \`copy_with_new_env\` to create a new instance."

ansible-playbook environment.yml 2>&1 | tee out.txt
grep out.txt -e "\[DEPRECATION WARNING\]: Direct access to the"
# the warning text is wrapped to the terminal width, so unwrap it before matching the full message
tr -s '[:space:]' ' ' < out.txt > out_unwrapped.txt
grep out_unwrapped.txt -e "Direct access to the \`environment\` attribute is deprecated. Consider using \`copy_with_new_env\` or passing \`overrides\` to \`template\`."

ansible-playbook unknown_type.yml 2>&1 | tee out.txt
grep out.txt -e "\[WARNING\]: Encountered unknown type 'UnknownType' during template operation."
# the warning text is wrapped to the terminal width, so unwrap it before matching the full message
tr -s '[:space:]' ' ' < out.txt > out_unwrapped.txt
grep out_unwrapped.txt -e "Encountered unknown type 'UnknownType' during template operation. Use supported types to avoid unexpected behavior."

ANSIBLE_ALLOW_BROKEN_CONDITIONALS=1 ansible-playbook empty_conditional.yml 2>&1 | tee out.txt
grep out.txt -e "\[DEPRECATION WARNING\]: Empty conditional expression was evaluated as True."
ANSIBLE_ALLOW_BROKEN_CONDITIONALS=0 ansible-playbook empty_conditional.yml 2>&1 | tee out.txt
grep out.txt -e "Empty conditional expressions are not allowed."
