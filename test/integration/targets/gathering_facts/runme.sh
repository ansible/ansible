#!/usr/bin/env bash

set -eux

# ANSIBLE_CACHE_PLUGINS=cache_plugins/ ANSIBLE_CACHE_PLUGIN=none ansible-playbook test_gathering_facts.yml -i ../../inventory -v "$@"
ansible-playbook test_gathering_facts.yml -i ../../inventory -v "$@"
#ANSIBLE_CACHE_PLUGIN=base ansible-playbook test_gathering_facts.yml -i ../../inventory -v "$@"

ANSIBLE_GATHERING=smart ansible-playbook test_run_once.yml -i ../../inventory -v "$@"

ANSIBLE_GATHERING=smart ansible-playbook test_smart_gathering.yml -i ../../inventory -v "$@"

# because facthost* are all the same host (localhost), tests are executed host by host,
# otherwise cleaning task of a play (/etc/ansible/facts.d/uuid.fact removal) will
# interfere with the next play
for host in facthost1 facthost2 facthost3 facthost4 facthost5 facthost6; do
    ANSIBLE_GATHERING=smart ansible-playbook test_smart_gathering_gather_subset.yml -i ../../inventory -l ${host} -v "$@"
done
