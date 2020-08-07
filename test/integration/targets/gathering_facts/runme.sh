#!/usr/bin/env bash

set -eux

# ANSIBLE_CACHE_PLUGINS=cache_plugins/ ANSIBLE_CACHE_PLUGIN=none ansible-playbook test_gathering_facts.yml -i inventory -v "$@"
ansible-playbook test_gathering_facts.yml -i inventory -v "$@"
# ANSIBLE_CACHE_PLUGIN=base ansible-playbook test_gathering_facts.yml -i inventory -v "$@"

ANSIBLE_GATHERING=smart ansible-playbook test_run_once.yml -i inventory -v "$@"

# ensure clean_facts is working properly
ansible-playbook test_prevent_injection.yml -i inventory -v "$@"

# ensure we dont clobber facts in loop
ansible-playbook prevent_clobbering.yml -v "$@"
