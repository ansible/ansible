#!/usr/bin/env bash

set -eux

# Test Fact Caching

export ANSIBLE_CACHE_PLUGIN="dummy_cache"

# test set_fact with cacheable: true
ansible-playbook test_fact_gathering.yml --tags set_fact "$@"
ansible-playbook inspect_cache.yml --tags set_fact "$@"

# cache gathered facts in addition
ansible-playbook test_fact_gathering.yml --tags gather_facts "$@"
ansible-playbook inspect_cache.yml --tags additive_gather_facts "$@"

# flush cache and only cache gathered facts
ansible-playbook test_fact_gathering.yml --flush-cache --tags gather_facts --tags flush "$@"
ansible-playbook inspect_cache.yml --tags gather_facts "$@"

unset ANSIBLE_CACHE_PLUGIN

# Test Inventory Caching

export ANSIBLE_INVENTORY_CACHE=true
export ANSIBLE_INVENTORY_CACHE_PLUGIN=dummy_cache

# Legacy cache plugins need to be updated to use set_options/get_option to be compatible with inventory plugins.
# Inventory plugins load cache options with the config manager.
ansible-playbook test_inventory_cache.yml "$@"

ansible-playbook inspect_inventory_cache.yml -i test.inventoryconfig.yml "$@"

# test file based cache with 'fun' inventory names
export ANSIBLE_CACHE_PLUGIN=dummy_file_cache ANSIBLE_CACHE_PLUGIN_CONNECTION="${OUTPUT_DIR}/dummy-file-cache"
mkdir -p "${ANSIBLE_CACHE_PLUGIN_CONNECTION}"
ansible-playbook -i chroot_inventory_config.yml invalid_hostname_file_caches.yml "$@"

# same, but using 'persistent' route
ANSIBLE_CACHE_PLUGIN=dummy_file_cache_persistent ansible-playbook -i chroot_inventory_config.yml invalid_hostname_file_caches.yml "$@"

# test file based cache with 'fun' inventory names, and a prefix!
export ANSIBLE_CACHE_PLUGIN_PREFIX="YOLO"
ansible-playbook -i chroot_inventory_config.yml invalid_hostname_file_caches.yml "$@"

ANSIBLE_CACHE_PLUGIN=dummy_file_cache_persistent ansible-playbook -i chroot_inventory_config.yml invalid_hostname_file_caches.yml "$@"
