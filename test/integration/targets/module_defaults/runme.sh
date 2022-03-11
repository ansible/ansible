#!/usr/bin/env bash

set -eux

sudo ln -s "${PWD}/collections/ansible_collections/testns/testcoll/plugins/action/vyos.py" ./collections/ansible_collections/testns/testcoll/plugins/action/vyos_facts.py

ansible-playbook test_defaults.yml "$@"

sudo rm ./collections/ansible_collections/testns/testcoll/plugins/action/vyos_facts.py

ansible-playbook test_action_groups.yml "$@"

ansible-playbook test_action_group_metadata.yml "$@"
