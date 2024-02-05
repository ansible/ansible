#!/usr/bin/env bash

set -eux

# Symlink is test for backwards-compat (only workaround for https://github.com/ansible/ansible/issues/77059)
sudo ln -s "${PWD}/collections/ansible_collections/testns/testcoll/plugins/action/vyos.py" ./collections/ansible_collections/testns/testcoll/plugins/action/vyosfacts.py

ansible-playbook test_defaults.yml "$@"

sudo rm ./collections/ansible_collections/testns/testcoll/plugins/action/vyosfacts.py

ansible-playbook test_action_groups.yml "$@"

ansible-playbook test_action_group_metadata.yml "$@"
