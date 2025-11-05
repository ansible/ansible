#!/usr/bin/env bash

set -eux

ansible-playbook -i inventory.ini test_types.yml "${@}"
ansible-playbook -v -i inventory.ini test_ansible_become.yml

ansible-inventory -v -i inventory.ini --list 2> out
test "$(grep -c 'SyntaxWarning' out)" -eq 0

cp inventory.ini inventory.toml

# check allowed_extensions, deprecation no setting
ansible-inventory -v -i inventory.toml --list >out 2>&1
test "$(grep -c 'Parsed inventory source with invalid extension' out)" -eq 0
test "$(grep -c 'testhost' out)" -ne 0

# check allowed_extensions, no deprecation when set
ANSIBLE_INVENTORY_PLUGIN_INI_EXT='toml' ansible-inventory -v -i inventory.toml --list >out 2>&1
test "$(grep -c 'Parsed inventory source with invalid extension' out)" -eq 0
test "$(grep -c 'testhost' out)" -ne 0

# check allowed_extensions, set to ini
ANSIBLE_INVENTORY_PLUGIN_INI_EXT='ini' ansible-inventory -v -i inventory.ini --list >out 2>&1
test "$(grep -c 'Parsed inventory source with invalid extension' out)" -eq 0
test "$(grep -c 'testhost' out)" -ne 0

# should not parse file at all and no msg
ANSIBLE_INVENTORY_PLUGIN_INI_EXT='ini' ansible-inventory -v -i inventory.toml --list >out 2>&1
test "$(grep -c 'Parsed inventory source with invalid extension' out)" -eq 0
test "$(grep -c 'testhost' out)" -eq 0
