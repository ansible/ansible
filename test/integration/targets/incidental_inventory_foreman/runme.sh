#!/usr/bin/env bash

[[ -n "$DEBUG" || -n "$ANSIBLE_DEBUG" ]] && set -x

set -euo pipefail

export ANSIBLE_INVENTORY
export ANSIBLE_PYTHON_INTERPRETER

unset ANSIBLE_INVENTORY
unset ANSIBLE_PYTHON_INTERPRETER

export ANSIBLE_CONFIG=ansible.cfg
export FOREMAN_HOST="${FOREMAN_HOST:-localhost}"
export FOREMAN_PORT="${FOREMAN_PORT:-8080}"
FOREMAN_CONFIG=test-config.foreman.yaml

# Set inventory caching environment variables to populate a jsonfile cache
export ANSIBLE_INVENTORY_CACHE=True
export ANSIBLE_INVENTORY_CACHE_PLUGIN=jsonfile
export ANSIBLE_INVENTORY_CACHE_CONNECTION=./foreman_cache

# flag for checking whether cleanup has already fired
_is_clean=

function _cleanup() {
    [[ -n "$_is_clean" ]] && return  # don't double-clean
    echo Cleanup: removing $FOREMAN_CONFIG...
    rm -vf "$FOREMAN_CONFIG"
    unset ANSIBLE_CONFIG
    unset FOREMAN_HOST
    unset FOREMAN_PORT
    unset FOREMAN_CONFIG
    _is_clean=1
}
trap _cleanup INT TERM EXIT

cat > "$FOREMAN_CONFIG" <<FOREMAN_YAML
plugin: foreman
url: http://${FOREMAN_HOST}:${FOREMAN_PORT}
user: ansible-tester
password: secure
validate_certs: False
FOREMAN_YAML

ansible-playbook test_foreman_inventory.yml --connection=local "$@"
ansible-playbook inspect_cache.yml --connection=local "$@"

# remove inventory cache
rm -r ./foreman_cache
