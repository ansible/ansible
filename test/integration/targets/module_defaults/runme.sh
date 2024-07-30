#!/usr/bin/env bash

set -eux

# Symlink is test for backwards-compat (only workaround for https://github.com/ansible/ansible/issues/77059)
sudo ln -s "${PWD}/collections/ansible_collections/testns/testcoll/plugins/action/vyos.py" ./collections/ansible_collections/testns/testcoll/plugins/action/vyosfacts.py

ANSIBLE_DEPRECATION_WARNINGS=true ansible-playbook test_defaults.yml "$@" 2> err.txt
test "$(grep -c 'testns.testcoll.old_ping has been deprecated' err.txt || 0)" -eq 0

sudo rm ./collections/ansible_collections/testns/testcoll/plugins/action/vyosfacts.py

ansible-playbook test_action_groups.yml "$@"

ansible-playbook test_action_group_metadata.yml "$@"
