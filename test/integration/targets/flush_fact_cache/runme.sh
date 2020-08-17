#!/usr/bin/env bash

set -eux

export ANSIBLE_GATHERING=explicit
export ANSIBLE_CACHE_PLUGIN=ansible.builtin.jsonfile
export ANSIBLE_CACHE_PLUGIN_CONNECTION=./cache_path/

function setup_fact_cache {
cat << EOF > "./cache_path/host1"
{
  "cached_fact": "exists"
}
EOF
}

### ansible-playbook
setup_fact_cache
ansible-playbook -i inventory.yml assert_cached_fact.yml -e 'result=exists' "$@"
ansible-playbook -i inventory.yml assert_cached_fact.yml --flush-cache -e "result=undefined" "$@"

### adhoc
setup_fact_cache
ansible -i inventory.yml host1 -m debug -a msg="{{ cached_fact | default('undefined') }}" "$@" | grep 'exists'
ansible -i inventory.yml host1 -m debug -a msg="{{ cached_fact | default('undefined') }}" --flush-cache "$@" | grep 'undefined'

### ansible-console
setup_fact_cache
ansible-console -i inventory.yml host1 "$@" << EOS
assert that="cached_fact | default('undefined') == 'exists'"
EOS
ansible-console -i inventory.yml host1 --flush-cache "$@" << EOS
assert that="cached_fact | default('undefined') == 'undefined'"
EOS

### ansible-inventory
setup_fact_cache
ansible-inventory -i inventory.yml --list "$@" | grep 'exists'
ansible-inventory -i inventory.yml --list --flush-cache "$@" | grep 'exists' && exit 1 || exit 0
