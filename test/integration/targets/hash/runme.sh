#!/usr/bin/env bash

set -eux

JSON_ARG='{"test_hash":{"extra_args":"this is an extra arg"}}'

ANSIBLE_HASH_BEHAVIOUR=replace ansible-playbook test_hash.yml -i inventory -v "$@" -e "${JSON_ARG}"
ANSIBLE_HASH_BEHAVIOUR=merge   ansible-playbook test_hash.yml -i inventory -v "$@" -e "${JSON_ARG}"
