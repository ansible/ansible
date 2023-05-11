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

# Test vars plugins aren't reloaded every time they might run
expected_debug=(
    "Loading VarsModule 'ansible_collections.testns.content_adj.plugins.vars.custom_adj_vars'"
    "Loading VarsModule 'v1_vars_plugin'"
    "Loading VarsModule 'v2_vars_plugin'"
    "Loading VarsModule 'host_group_vars'"
)
verbose_result="$(ANSIBLE_DEBUG=True ansible-playbook test_task_vars.yml)"

test "$(grep -c "Loading VarsModule" <<< "$verbose_result")" == 4
for plugin in "$expected_debug"; do
    test "$(grep -c "$plugin" <<< "$verbose_result")" == 1;
done

# Test how many times vars plugins run
# Not collection-specific - move to a different test target?
cat << EOF > "test_exe_vars_plugins.yml"
---
- hosts: localhost
  gather_facts: no
  tasks:
  - debug: msg="{{ adj_var }}"
  - debug: msg="{{ adj_var }}"
EOF

cat << EOF > "empty_inventory"
EOF

# * After parsing inventory, the vars plugin should run 2 times (2 entities x 1 location).
#   The inventory is empty, so the default entities are the groups 'all' and 'ungrouped'.
# * The vars plugin should run 30 times for the task list (5 tasks x 3 entities x 2 locations).
#   The tasks list contains an implicit flush handlers, 2 debug tasks, and 2 more implicit flush handlers.
#   The entities are the group 'all', the groups of the host (empty in this case) and the host (localhost).
#   Playbook adjacent locations are searched in addition to inventory adjacent.
ANSIBLE_DEBUG=True ansible-playbook -i empty_inventory test_exe_vars_plugins.yml | grep -e "Executing VarsModule"
test "$(ANSIBLE_DEBUG=True ansible-playbook -i empty_inventory test_exe_vars_plugins.yml | grep -c "Executing VarsModule")" == 32

# Note: excluding inventory-adjacent vars by using host list
export ANSIBLE_VARS_PLUGIN_STAGE=inventory
test "$(ANSIBLE_DEBUG=True ansible-playbook -i , test_exe_vars_plugins.yml | grep -c "Executing VarsModule")" == 0
test "$(ANSIBLE_DEBUG=True ansible-playbook -i empty_inventory test_exe_vars_plugins.yml | grep -c "Executing VarsModule")" == 2

# 5 tasks * 3 entities * 1 location
unset ANSIBLE_VARS_PLUGIN_STAGE
test "$(ANSIBLE_DEBUG=True ansible-playbook -i , test_exe_vars_plugins.yml | grep -c "Executing VarsModule")" == 15
