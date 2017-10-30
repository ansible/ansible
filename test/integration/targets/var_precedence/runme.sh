#!/usr/bin/env bash

set -eux

MYTMPDIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')
trap 'rm -rf "${MYTMPDIR}"' EXIT

# no fact caching
ansible-playbook test_var_precedence.yml -i ../../inventory -v "$@" \
    -e 'extra_var=extra_var' \
    -e 'extra_var_override=extra_var_override' \
    -e '{ write_cache: False }'

# use fact cache, and invoke set_fact with 'cacheable=true' so we can test it across plays in a playbook
ANSIBLE_CACHE_PLUGIN=jsonfile ANSIBLE_CACHE_PLUGIN_CONNECTION="${MYTMPDIR}" ansible-playbook test_var_precedence.yml -i ../../inventory -v "$@" \
    -e 'extra_var=extra_var' \
    -e 'extra_var_override=extra_var_override' \
    -e '{ write_cache: True }'

# use fact cache, but do not use set_fact with 'cacheable=true' so no set_fact calls should persist across plays in a playbook
ANSIBLE_CACHE_PLUGIN=jsonfile ANSIBLE_CACHE_PLUGIN_CONNECTION="${MYTMPDIR}" ansible-playbook test_var_precedence.yml -i ../../inventory -v "$@" \
    -e 'extra_var=extra_var' \
    -e 'extra_var_override=extra_var_override' \
    -e '{ write_cache: False }'
