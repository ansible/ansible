#!/usr/bin/env bash

set -eux

MYTMPDIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')
trap 'rm -rf "${MYTMPDIR}"' EXIT

ANSIBLE_CACHE_PLUGIN=jsonfile ANSIBLE_CACHE_PLUGIN_CONNECTION="${MYTMPDIR}" ansible-playbook -i ../../inventory "$@" set_fact_cached_1.yml

ANSIBLE_CACHE_PLUGIN=jsonfile ANSIBLE_CACHE_PLUGIN_CONNECTION="${MYTMPDIR}" ansible-playbook -i ../../inventory "$@" set_fact_cached_2.yml

ANSIBLE_CACHE_PLUGIN=jsonfile ANSIBLE_CACHE_PLUGIN_CONNECTION="${MYTMPDIR}" ansible-playbook -i ../../inventory --flush-cache "$@" set_fact_no_cache.yml

