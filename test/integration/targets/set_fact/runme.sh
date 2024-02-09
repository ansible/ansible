#!/usr/bin/env bash

set -eux

MYTMPDIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')
trap 'rm -rf "${MYTMPDIR}"' EXIT

# ensure we can incrementally set fact via loopi, injection or not
ANSIBLE_INJECT_FACT_VARS=0 ansible-playbook -i inventory incremental.yml
ANSIBLE_INJECT_FACT_VARS=1 ansible-playbook -i inventory incremental.yml

# ensure we dont have spurious warnings do to clean_facts
ansible-playbook -i inventory nowarn_clean_facts.yml | grep '[WARNING]: Removed restricted key from module data: ansible_ssh_common_args' && exit 1

# test cached feature
export ANSIBLE_CACHE_PLUGIN=jsonfile ANSIBLE_CACHE_PLUGIN_CONNECTION="${MYTMPDIR}" ANSIBLE_CACHE_PLUGIN_PREFIX=prefix_
ansible-playbook -i inventory "$@" set_fact_cached_1.yml
ansible-playbook -i inventory "$@" set_fact_cached_2.yml

# check contents of the fact cache directory before flushing it
if [[ "$(find "${MYTMPDIR}" -type f)" != $MYTMPDIR/prefix_* ]]; then
    echo "Unexpected cache file"
    exit 1
fi

ansible-playbook -i inventory --flush-cache "$@" set_fact_no_cache.yml

# Test boolean conversions in set_fact
ANSIBLE_JINJA2_NATIVE=0 ansible-playbook -v set_fact_bool_conv.yml
ANSIBLE_JINJA2_NATIVE=1 ansible-playbook -v set_fact_bool_conv_jinja2_native.yml

# Test parsing of values when using an empty string as a key
ansible-playbook -i inventory set_fact_empty_str_key.yml

# https://github.com/ansible/ansible/issues/21088
ansible-playbook -i inventory "$@" set_fact_auto_unsafe.yml

ansible-playbook -i inventory "$@" set_fact_ansible_vars.yml 2>&1 | tee test_set_fact_ansible_vars.out
test "$(grep -E -c 'is reserved for internal use only.' test_set_fact_ansible_vars.out)" = 1
