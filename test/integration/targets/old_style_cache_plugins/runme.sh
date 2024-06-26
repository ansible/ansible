#!/usr/bin/env bash

set -eux

source virtualenv.sh

trap 'ansible-playbook cleanup.yml' EXIT

export PATH="$PATH:/usr/local/bin"

ansible-playbook setup_redis_cache.yml "$@"

# Cache should start empty
redis-cli keys ansible_
[ "$(redis-cli keys ansible_)" = "" ]

export ANSIBLE_CACHE_PLUGINS=./plugins/cache
export ANSIBLE_CACHE_PLUGIN_CONNECTION=localhost:6379:0
export ANSIBLE_CACHE_PLUGIN_PREFIX='ansible_facts_'

# Test legacy cache plugins (that use ansible.constants) and
# new cache plugins that use config manager both work for facts.
for fact_cache in legacy_redis configurable_redis; do

    export ANSIBLE_CACHE_PLUGIN="$fact_cache"

    # test set_fact with cacheable: true
    ansible-playbook test_fact_gathering.yml --tags set_fact "$@"
    [ "$(redis-cli keys ansible_facts_localhost | wc -l)" -eq 1 ]
    ansible-playbook inspect_cache.yml --tags set_fact "$@"

    # cache gathered facts in addition
    ansible-playbook test_fact_gathering.yml --tags gather_facts "$@"
    ansible-playbook inspect_cache.yml --tags additive_gather_facts "$@"

    # flush cache and only cache gathered facts
    ansible-playbook test_fact_gathering.yml --flush-cache --tags gather_facts --tags flush "$@"
    ansible-playbook inspect_cache.yml --tags gather_facts "$@"

    redis-cli del ansible_facts_localhost
    unset ANSIBLE_CACHE_PLUGIN

done

# Legacy cache plugins need to be updated to use set_options/get_option to be compatible with inventory plugins.
# Inventory plugins load cache options with the config manager.
ansible-playbook test_inventory_cache.yml "$@"
