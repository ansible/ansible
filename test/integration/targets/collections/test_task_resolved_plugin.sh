#!/usr/bin/env bash

set -eux

export ANSIBLE_CALLBACKS_ENABLED=display_resolved_action

ansible-playbook test_task_resolved_plugin/unqualified.yml "$@" | tee out.txt
action_resolution=(
    "legacy_action == legacy_action"
    "legacy_module == legacy_module"
    "debug == ansible.builtin.debug"
    "ping == ansible.builtin.ping"
)
for result in "${action_resolution[@]}"; do
    grep -q out.txt -e "$result"
done

# Test local_action/action warning
export ANSIBLE_TEST_ON_TASK_START=True
ansible-playbook -i debug, test_task_resolved_plugin/dynamic_action.yml "$@" 2>&1 | tee out.txt
grep -q out.txt -e "A plugin is sampling the task's resolved_action when it is not resolved"
grep -q out.txt -e "v2_playbook_on_task_start: {{ inventory_hostname }} == None"
grep -q out.txt -e "v2_runner_on_ok: debug == ansible.builtin.debug"
grep -q out.txt -e "v2_runner_item_on_ok: debug == ansible.builtin.debug"

# Test static actions don't cause a warning
ansible-playbook test_task_resolved_plugin/unqualified.yml "$@" 2>&1 | tee out.txt
grep -v out.txt -e "A plugin is sampling the task's resolved_action when it is not resolved"
for result in "${action_resolution[@]}"; do
    grep -q out.txt -e "v2_playbook_on_task_start: $result"
done
unset ANSIBLE_TEST_ON_TASK_START

ansible-playbook test_task_resolved_plugin/unqualified_and_collections_kw.yml "$@" | tee out.txt
action_resolution=(
    "legacy_action == legacy_action"
    "legacy_module == legacy_module"
    "debug == ansible.builtin.debug"
    "ping == ansible.builtin.ping"
    "collection_action == test_ns.test_coll.collection_action"
    "collection_module == test_ns.test_coll.collection_module"
    "formerly_action == test_ns.test_coll.collection_action"
    "formerly_module == test_ns.test_coll.collection_module"
)
for result in "${action_resolution[@]}"; do
    grep -q out.txt -e "$result"
done

ansible-playbook test_task_resolved_plugin/fqcn.yml "$@" | tee out.txt
action_resolution=(
    "ansible.legacy.legacy_action == legacy_action"
    "ansible.legacy.legacy_module == legacy_module"
    "ansible.legacy.debug == ansible.builtin.debug"
    "ansible.legacy.ping == ansible.builtin.ping"
    "ansible.builtin.debug == ansible.builtin.debug"
    "ansible.builtin.ping == ansible.builtin.ping"
    "test_ns.test_coll.collection_action == test_ns.test_coll.collection_action"
    "test_ns.test_coll.collection_module == test_ns.test_coll.collection_module"
    "test_ns.test_coll.formerly_action == test_ns.test_coll.collection_action"
    "test_ns.test_coll.formerly_module == test_ns.test_coll.collection_module"
)
for result in "${action_resolution[@]}"; do
    grep -q out.txt -e "$result"
done
