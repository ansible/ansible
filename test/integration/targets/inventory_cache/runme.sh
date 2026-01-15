#!/usr/bin/env bash

set -eux

export ANSIBLE_INVENTORY_PLUGINS=./plugins/inventory

cleanup() {
    rm -rf ./cache/ansible_inventory* ./vault_cache
    rm -f vault.pass vaulted_run*.json vaulted.yml temp_*.yml bytes_vaulted.yml bytes_run*.json out.txt
}

trap 'cleanup' EXIT

# Basic cache consistency
test "$(ansible-inventory -i cache_host.yml --graph 2>&1 | tee out.txt | grep -c '\[WARNING\]')" = 0
writehost="$(grep "testhost[0-9]\{1,2\}" out.txt)"

test "$(ansible-inventory -i cache_host.yml --graph 2>&1 | tee out.txt | grep -c '\[WARNING\]')" = 0
readhost="$(grep 'testhost[0-9]\{1,2\}' out.txt)"

test "$readhost" = "$writehost"

ansible-inventory -i exercise_cache.yml --graph

# Vault serialization tests
echo "password" > vault.pass
export ANSIBLE_VAULT_PASSWORD_FILE="${PWD}/vault.pass"

mkdir -p ./vault_cache
export ANSIBLE_INVENTORY_CACHE=True
export ANSIBLE_INVENTORY_CACHE_PLUGIN=jsonfile
export ANSIBLE_INVENTORY_CACHE_CONNECTION="${PWD}/vault_cache"

cat > vaulted.yml <<EOF
all:
  hosts:
    vaulted_host:
EOF

ansible-vault encrypt_string 'secret' --name 'my_secret' | sed 's/^/      /' >> vaulted.yml

echo "      vaulted_list:" >> vaulted.yml
echo "        - plain_item" >> vaulted.yml
ansible-vault encrypt_string 'list_secret' --name 'placeholder' \
    | sed 's/^placeholder:/-/' | sed 's/^/        /' >> vaulted.yml

echo "      vaulted_dict:" >> vaulted.yml
echo "        plain_key: plain_value" >> vaulted.yml
ansible-vault encrypt_string 'dict_secret' --name 'secret_key' \
    | sed 's/^/        /' >> vaulted.yml

ansible-inventory -i vaulted.yml --list > vaulted_run1.json
ansible-inventory -i vaulted.yml --list > vaulted_run2.json

grep -q '"my_secret": "secret"' vaulted_run2.json
grep -q '"list_secret"' vaulted_run2.json
grep -q '"secret_key": "dict_secret"' vaulted_run2.json

# Bytes serialization tests
cat > bytes_vaulted.yml <<EOF
plugin: vaulted_test_plugin
cache: true
cache_plugin: jsonfile
cache_connection: ./vault_cache
EOF

ansible-inventory -i bytes_vaulted.yml --list > bytes_run1.json
ansible-inventory -i bytes_vaulted.yml --list > bytes_run2.json

grep -q '"my_bytes": "byte_string"' bytes_run2.json
