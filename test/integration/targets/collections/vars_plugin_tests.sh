#!/usr/bin/env bash

set -eux

# Collections vars plugins must be enabled using the FQCN in the 'enabled' list, because PluginLoader.all() does not search collections

# Let vars plugins run for inventory by using the global setting
export ANSIBLE_RUN_VARS_PLUGINS=start

# Test vars plugin in a playbook-adjacent collection
export ANSIBLE_VARS_ENABLED=testns.content_adj.custom_adj_vars

ansible-inventory -i a.statichost.yml --list --playbook-dir=./ 2>&1 | tee out.txt

grep '"collection": "adjacent"' out.txt
grep '"adj_var": "value"' out.txt
grep -v "REQUIRES_ENABLED is not supported" out.txt

# Test vars plugin in a collection path
export ANSIBLE_VARS_ENABLED=testns.testcoll.custom_vars
export ANSIBLE_COLLECTIONS_PATH=$PWD/collection_root_user:$PWD/collection_root_sys

ansible-inventory -i a.statichost.yml --list --playbook-dir=./ 2>&1 | tee out.txt

grep '"collection": "collection_root_user"' out.txt
grep -v '"adj_var": "value"' out.txt
grep "REQUIRES_ENABLED is not supported" out.txt

# Test enabled vars plugins order reflects the order in which variables are merged
export ANSIBLE_VARS_ENABLED=testns.content_adj.custom_adj_vars,testns.testcoll.custom_vars

ansible-inventory -i a.statichost.yml --list --playbook-dir=./ | tee out.txt

grep '"collection": "collection_root_user"' out.txt
grep '"adj_var": "value"' out.txt
grep -v '"collection": "adjacent"' out.txt

# Test that 3rd party plugins in plugin_path do not need to require enabling by default
# Plugins shipped with Ansible and in the custom plugin dir should be used first
export ANSIBLE_VARS_PLUGINS=./custom_vars_plugins

ansible-inventory -i a.statichost.yml --list --playbook-dir=./ | tee out.txt

grep '"name": "v2_vars_plugin"' out.txt
grep '"collection": "collection_root_user"' out.txt
grep '"adj_var": "value"' out.txt

# Test plugins in plugin paths that opt-in to require enabling
unset ANSIBLE_VARS_ENABLED
unset ANSIBLE_COLLECTIONS_PATH


# Test vars plugins that support the stage setting don't run for inventory when stage is set to 'task'
# and that the vars plugins that don't support the stage setting don't run for inventory when the global setting is 'demand'
ANSIBLE_VARS_PLUGIN_STAGE=task ansible-inventory -i a.statichost.yml --list --playbook-dir=./ | tee out.txt

grep -v '"v1_vars_plugin": true' out.txt
grep -v '"v2_vars_plugin": true' out.txt
grep -v '"collection": "adjacent"' out.txt
grep -v '"collection": "collection_root_user"' out.txt
grep -v '"adj_var": "value"' out.txt

# Test that the global setting allows v1 and v2 plugins to run after importing inventory
ANSIBLE_RUN_VARS_PLUGINS=start ansible-inventory -i a.statichost.yml --list --playbook-dir=./ | tee out.txt

grep '"v1_vars_plugin": true' out.txt
grep '"v2_vars_plugin": true' out.txt
grep '"name": "v2_vars_plugin"' out.txt

# Test that vars plugins in collections and in the vars plugin path are available for tasks
cat << EOF > "test_task_vars.yml"
---
- hosts: localhost
  connection: local
  gather_facts: no
  tasks:
  - debug: msg="{{ name }}"
  - debug: msg="{{ collection }}"
  - debug: msg="{{ adj_var }}"
EOF

export ANSIBLE_VARS_ENABLED=testns.content_adj.custom_adj_vars

ANSIBLE_VARS_PLUGIN_STAGE=task ANSIBLE_VARS_PLUGINS=./custom_vars_plugins ansible-playbook test_task_vars.yml | grep "ok=3"
ANSIBLE_RUN_VARS_PLUGINS=start ANSIBLE_VARS_PLUGIN_STAGE=inventory ANSIBLE_VARS_PLUGINS=./custom_vars_plugins ansible-playbook test_task_vars.yml | grep "ok=3"
ANSIBLE_RUN_VARS_PLUGINS=demand ANSIBLE_VARS_PLUGIN_STAGE=inventory ANSIBLE_VARS_PLUGINS=./custom_vars_plugins ansible-playbook test_task_vars.yml | grep "ok=3"
ANSIBLE_VARS_PLUGINS=./custom_vars_plugins ansible-playbook test_task_vars.yml | grep "ok=3"
