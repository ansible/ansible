#!/usr/bin/env bash

set -eux

# ANSIBLE_CACHE_PLUGINS=cache_plugins/ ANSIBLE_CACHE_PLUGIN=none ansible-playbook test_gathering_facts.yml -i ../../inventory -v "$@"
ansible-playbook test_gathering_facts.yml -i ../../inventory -v "$@"
#ANSIBLE_CACHE_PLUGIN=base ansible-playbook test_gathering_facts.yml -i ../../inventory -v "$@"
