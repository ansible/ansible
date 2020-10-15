#!/usr/bin/env bash
set -eux

cache_dir="$(pwd)/jsonfile_cache/"
plugin_dir="$(pwd)/plugins/inventory/"

export ANSIBLE_CACHE_PLUGIN=jsonfile
export ANSIBLE_CACHE_PLUGIN_CONNECTION=${cache_dir}
export ANSIBLE_CACHE_PLUGIN_TIMEOUT=20
export ANSIBLE_CACHE_PLUGIN_PREFIX=''
export ANSIBLE_INVENTORY_PLUGINS=${plugin_dir}

ansible-playbook -i ./inventory.yml test_populate_cache.yml "$@"
ansible-playbook -i ./inventory.yml test_use_cache.yml "$@"
