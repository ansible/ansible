#!/usr/bin/env bash

set -o errexit -o nounset -o xtrace

export ANSIBLE_INVENTORY_PLUGINS=./
export ANSIBLE_INVENTORY_ENABLED=test_inventory

# check default values
ansible-inventory --list -i ./config_without_parameter.yml --export | \
    env python -c "import json, sys; inv = json.loads(sys.stdin.read()); \
                   assert set(inv['_meta']['hostvars']['test_host']['departments']) == set(['seine-et-marne', 'haute-garonne'])"

# check values
ansible-inventory --list -i ./config_with_parameter.yml --export | \
    env python -c "import json, sys; inv = json.loads(sys.stdin.read()); \
                   assert set(inv['_meta']['hostvars']['test_host']['departments']) == set(['paris'])"

secret=$(ansible-vault encrypt_string 'secret' --vault-password-file ./password_file)

cat << EOF > "config.yml"
plugin: test_inventory
vaulted_option: $secret
templateable_option: "{{ template_me }}"
ignore_template: "{{ do_not_template_me }}"
EOF

export ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED=False
ansible-inventory -i ./config.yml --vault-password-file ./password_file --list 2>&1 | grep "'template_me' is undefined"

unset ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED
ansible-inventory -i ./config.yml -e template_me='templated' --vault-password-file ./password_file --list | tee out.txt

grep '"ignore_template": "{{ do_not_template_me }}"' out.txt
grep '"inline_vault": "secret"' out.txt
grep '"template": "templated"' out.txt
grep '"template_me": "templated"' out.txt
