#!/usr/bin/env bash

set -eux

JSON_ARG='{"test_hash":{"extra_args":"this is an extra arg","test_list": [ { "name":"this is an extra arg" } ]}}'

# default
ANSIBLE_HASH_BEHAVIOUR=replace ANSIBLE_LIST_BEHAVIOUR=replace  ansible-playbook test_hash.yml -i ../../inventory -v "$@" -e "${JSON_ARG}"

# current unexpected merge behaviour with replaced lists
ANSIBLE_HASH_BEHAVIOUR=merge ANSIBLE_LIST_BEHAVIOUR=replace ansible-playbook test_hash.yml -i ../../inventory -v "$@" -e "${JSON_ARG}"

# merge hashes and nested lists
ANSIBLE_HASH_BEHAVIOUR=merge ANSIBLE_LIST_BEHAVIOUR=merge  ansible-playbook test_hash.yml -i ../../inventory -v "$@" -e "${JSON_ARG}"

# list only
ANSIBLE_HASH_BEHAVIOUR=replace ANSIBLE_LIST_BEHAVIOUR=merge  ansible-playbook test_hash.yml -i ../../inventory -v "$@" -e "${JSON_ARG}"
