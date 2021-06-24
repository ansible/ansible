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
