#!/usr/bin/env bash

set -ux
set +e

# Check that one source fails, as expected
ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED=yes ansible-inventory -i partially_bad_source --list
if [[ $? -ne 1 ]]; then
    exit 1
fi

set -e

# Check that a warning is given when inventory is restored from an incomplete state
ANSIBLE_INVENTORY_UNPARSED_FAILED=yes ANSIBLE_INVENTORY_ENABLED=ini ansible-inventory -i partially_bad_source --list 2>&1 | tee out.txt
if [[ "$(grep -c out.txt -e 'restoring inventory')" -ne 1 ]] ; then
    echo "Did not get warning when an inventory source was partially parsed"
    exit 1
fi

# Check that a warning is only given when inventory incorrectly changes, not just when a source fails to be parsed
ANSIBLE_INVENTORY_UNPARSED_FAILED=yes ansible-inventory -i one_valid_and_invalid_source/ --list 2>&1 | tee out.txt
if [[ "$(grep -c out.txt -e 'restoring inventory')" -ne 0 ]] ; then
    echo "Got a warning for an inventory source that should not have partially modified inventory"
    exit 1
fi

# Check that vars added to hosts and groups are removed if the source does not completely parse
ANSIBLE_INVENTORY_UNPARED_FAILED=yes ansible-inventory -i partially_bad_source_test_remove_var/ --list | tee out.txt
if [[ "$(grep -c out.txt -e 'group_var')" -ne 0 ]]
   [[ "$(grep -c out.txt -e 'host_var')" -ne 0 ]] ; then
    echo "Found a residual variable from a failed inventory source"
    exit 1
elif [[ "$(grep -c out.txt -e 'master_only')" -ne 2 ]] ||
     [[ "$(grep -c out.txt -e 'tags')" -ne 3 ]] ; then
    echo "Expected variables from successful source are missing"
    exit 1
fi

# Check that inventory only contains data from successful sources
ANSIBLE_INVENTORY_UNPARSED_FAILED=yes ansible-inventory -i partially_bad_source --list | tee out.txt

if [[ "$(grep -c out.txt -e 'ansible_become')" -ne 0 ]] ||
   [[ "$(grep -c out.txt -e 'ansible_ssh_user')" -ne 0 ]] ||
   [[ "$(grep -c out.txt -e 'scp_if_ssh')" -ne 0 ]] ||
   [[ "$(grep -c out.txt -e 'containerized')" -ne 0 ]] ; then
    echo "Found a hostvar from a failed inventory source"
    exit 1
elif [[ "$(grep -c out.txt -e 'foo')" -ne 5 ]] ||
     [[ "$(grep -c out.txt -e 'master_only')" -ne 2 ]] ||
     [[ "$(grep -c out.txt -e 'tags')" -ne 3 ]] ; then
    echo "Did not find expected hostvars from successful inventory source"
    exit 1
fi

# Test that the restored inventory after partially parsing a bad source matches using only the good source
ANSIBLE_INVENTORY_ANY_UNPARSED_FAILED=yes ansible-playbook -i groups_of_groups/a test_groups_of_groups.yml
ANSIBLE_INVENTORY_UNPARSED_FAILED=yes ansible-playbook -i groups_of_groups test_groups_of_groups.yml

# Check that displayed inventory does not duplicate hosts per group
ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED=yes ansible-inventory -i source_with_duplication --graph | tee out.txt
if [[ "$(grep -c out.txt -e 'master0')" -ne 1 ]] ||
   [[ "$(grep -c out.txt -e 'node0')" -ne 1 ]] ||
   [[ "$(grep -c out.txt -e 'node1')" -ne 1 ]] ||
   [[ "$(grep -c out.txt -e 'node2')" -ne 1 ]] ; then
    echo "Did not find expected unique hosts per group"
    exit 1
fi
