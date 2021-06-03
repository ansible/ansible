#!/usr/bin/env bash

set -eux

ANSIBLE_STDOUT_CALLBACK=display_resolved_action ansible-playbook playbook.yml "$@" | tee out.txt

#### Test action/module callback banners from a playbook

# Called as:
# - custom_module + collections kw
# - test_ns.test_coll.custom_module
# - redirected_module + collections kw
# - test_ns.test_coll.redirected_module
test "$(grep -c out.txt -e '\[test_ns.test_coll.custom_module\]')" == 4

# Called as:
# - custom_action + collections kw
# - test_ns.test_coll.custom_action
# - redirected_action + collections kw
# - test_ns.test_coll.redirected_action
test "$(grep -c out.txt -e '\[test_ns.test_coll.custom_action\]')" == 4

# Called as:
# - legacy_module
# - legacy_module + collections kw
# - ansible.legacy.legacy_module
test "$(grep -c out.txt -e '\[legacy_module\]')" == 3

# Called as:
# - legacy_action
# - legacy_action + collections kw
# - ansible.legacy.legacy_action
test "$(grep -c out.txt -e '\[legacy_action\]')" == 3

#### Test action/module callback banners from a legacy role

test "$(grep -c out.txt -e '\[legacy_role : test_ns.test_coll.custom_module\]')" == 1
test "$(grep -c out.txt -e '\[legacy_role : test_ns.test_coll.custom_action\]')" == 1
test "$(grep -c out.txt -e '\[legacy_role : legacy_module\]')" == 1
test "$(grep -c out.txt -e '\[legacy_role : legacy_action\]')" == 1

#### Test action/module callback banners from a collection's role

test "$(grep -c out.txt -e '\[test_ns.test_coll.collection_role : test_ns.test_coll.custom_module\]')" == 1
test "$(grep -c out.txt -e '\[test_ns.test_coll.collection_role : test_ns.test_coll.custom_action\]')" == 1
test "$(grep -c out.txt -e '\[test_ns.test_coll.collection_role : legacy_module\]')" == 1
test "$(grep -c out.txt -e '\[test_ns.test_coll.collection_role : legacy_action\]')" == 1
