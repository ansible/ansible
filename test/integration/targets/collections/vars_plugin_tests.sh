#!/usr/bin/env bash

set -eux

# Collections vars plugins must be whitelisted with FQCN because PluginLoader.all() does not search collections

# Test adjacent vars plugin
ANSIBLE_VARS_ENABLED=testns.content_adj.custom_adj_vars ansible-inventory -i a.statichost.yml --list --playbook-dir=./ | tee out.txt

grep '"collection": "adjacent"' out.txt
grep '"adj_var": "value"' out.txt

# Test vars plugin in a collection path
export ANSIBLE_COLLECTIONS_PATHS=$PWD/collection_root_user:$PWD/collection_root_sys

ANSIBLE_VARS_ENABLED=testns.testcoll.custom_vars ansible-inventory -i a.statichost.yml --list --playbook-dir=./ | tee out.txt

grep '"collection": "collection_root_user"' out.txt
grep -v '"adj_var": "value"' out.txt

# Test enabled vars plugins order reflects the order in which variables are merged
export ANSIBLE_VARS_ENABLED=testns.content_adj.custom_adj_vars,testns.testcoll.custom_vars

ansible-inventory -i a.statichost.yml --list --playbook-dir=./ | tee out.txt

grep '"collection": "collection_root_user"' out.txt
grep '"adj_var": "value"' out.txt
grep -v '"collection": "adjacent"' out.txt

# Test that 3rd party plugin in plugin_path does not need whitelisting by default
# Plugins shipped with Ansible and in the custom plugin dir should be used first
ANSIBLE_VARS_PLUGINS=./custom_vars_plugins ansible-inventory -i a.statichost.yml --list --playbook-dir=./ | tee out.txt

grep '"foo": "bar"' out.txt
grep '"collection": "collection_root_user"' out.txt
grep '"adj_var": "value"' out.txt
grep -v '"whitelisted": true' out.txt

# Test plugins in plugin paths that require whitelisting
ANSIBLE_VARS_ENABLED=vars_req_whitelist ANSIBLE_VARS_PLUGINS=./custom_vars_plugins ansible-inventory -i a.statichost.yml --list --playbook-dir=./ | tee out.txt
grep '"whitelisted": true' out.txt

# Test settings to determine when vars plugins run
ANSIBLE_VARS_PLUGIN_STAGE=task ANSIBLE_VARS_PLUGINS=./custom_vars_plugins ansible-inventory -i a.statichost.yml --list --playbook-dir=./ | tee out.txt

grep -v '"foo": "bar"' out.txt
grep -v '"collection": "collection_root_user"' out.txt
grep -v '"adj_var": "value"' out.txt

cat << EOF > "test_task_vars.yml"
---
- hosts: localhost
  connection: local
  gather_facts: no
  tasks:
  - debug: msg="{{ foo }}"
  - debug: msg="{{ collection }}"
  - debug: msg="{{ adj_var }}"
EOF

ANSIBLE_VARS_PLUGIN_STAGE=task ANSIBLE_VARS_PLUGINS=./custom_vars_plugins ansible-playbook test_task_vars.yml | grep "ok=3"
ANSIBLE_RUN_VARS_PLUGINS=start ANSIBLE_VARS_PLUGIN_STAGE=inventory ANSIBLE_VARS_PLUGINS=./custom_vars_plugins ansible-playbook test_task_vars.yml | grep "ok=3"
