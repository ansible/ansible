#!/usr/bin/env bash

set -eux

# Hosts in playbook has a list of strings consisting solely of digits
ansible-playbook test_hosts_field.yml -i inventory.hosts_field -e 'target_kv=42' \
    -e '{ "target_json_cli": "42", "target_json_cli_list": ["42", "localhost"] }' -e "@test_hosts_field.json" \
    -t string_digit_host_in_list -v "$@" | tee test_hosts_field.out
grep 'Running on 42' test_hosts_field.out 2>&1
test "$(grep -c 'ok=1' test_hosts_field.out)" = 1

# Hosts taken from kv extra_var on the CLI
ansible-playbook test_hosts_field.yml -i inventory.hosts_field -e 'target_kv=42' \
    -e '{ "target_json_cli": "42", "target_json_cli_list": ["42", "localhost"] }' -e "@test_hosts_field.json" \
    -t hosts_from_kv_string -v "$@" | tee test_hosts_field.out
grep 'Running on 42' test_hosts_field.out 2>&1
test "$(grep -c 'ok=1' test_hosts_field.out)" = 1

# hosts is taken from an all digit json extra_vars string on the CLI
ansible-playbook test_hosts_field.yml -i inventory.hosts_field -e 'target_kv=42' \
    -e '{ "target_json_cli": "42", "target_json_cli_list": ["42", "localhost"] }' -e "@test_hosts_field.json" \
    -t hosts_from_cli_json_string -v "$@" | tee test_hosts_field.out
grep 'Running on 42' test_hosts_field.out 2>&1
test "$(grep -c 'ok=1' test_hosts_field.out)" = 1

# hosts is taken from a json list in extra_vars on the CLI
ansible-playbook test_hosts_field.yml -i inventory.hosts_field -e 'target_kv=42' \
    -e '{ "target_json_cli": "42", "target_json_cli_list": ["42", "localhost"] }' -e "@test_hosts_field.json" \
    -t hosts_from_cli_json_list -v "$@" | tee test_hosts_field.out
grep 'Running on 42' test_hosts_field.out 2>&1
grep 'Running on localhost' test_hosts_field.out 2>&1
test "$(grep -c 'ok=1' test_hosts_field.out)" = 2

# hosts is taken from a json string in an extra_vars file
ansible-playbook test_hosts_field.yml -i inventory.hosts_field -e 'target_kv=42' \
    -e '{ "target_json_cli": "42", "target_json_cli_list": ["42", "localhost"] }' -e "@test_hosts_field.json" \
    -t hosts_from_json_file_string -v "$@" | tee test_hosts_field.out
grep 'Running on 42' test_hosts_field.out 2>&1
test "$(grep -c 'ok=1' test_hosts_field.out)" = 1

# hosts is taken from a json list in an extra_vars file
ansible-playbook test_hosts_field.yml -i inventory.hosts_field -e 'target_kv=42' \
    -e '{ "target_json_cli": "42", "target_json_cli_list": ["42", "localhost"] }' -e "@test_hosts_field.json" \
    -t hosts_from_json_file_list -v "$@" | tee test_hosts_field.out
grep 'Running on 42' test_hosts_field.out 2>&1
grep 'Running on localhost' test_hosts_field.out 2>&1
test "$(grep -c 'ok=1' test_hosts_field.out)" = 2

rm test_hosts_field.out
