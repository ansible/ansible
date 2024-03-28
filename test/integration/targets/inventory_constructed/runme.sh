#!/usr/bin/env bash

set -eux

ansible-inventory -i static_inventory.yml -i constructed.yml --graph | tee out.txt

grep '@_hostvalue1' out.txt
grep '@_item0' out.txt
grep '@_key0_value0' out.txt
grep '@prefix_hostvalue1' out.txt
grep '@prefix_item0' out.txt
grep '@prefix_key0_value0' out.txt
grep '@separatorhostvalue1' out.txt
grep '@separatoritem0' out.txt
grep '@separatorkey0separatorvalue0' out.txt

ansible-inventory -i static_inventory.yml -i no_leading_separator_constructed.yml --graph | tee out.txt

grep '@hostvalue1' out.txt
grep '@item0' out.txt
grep '@key0_value0' out.txt
grep '@key0separatorvalue0' out.txt
grep '@prefix_hostvalue1' out.txt
grep '@prefix_item0' out.txt
grep '@prefix_key0_value0' out.txt

# keyed group with default value for key's value empty (dict)
ansible-inventory -i tag_inventory.yml -i keyed_group_default_value.yml --graph | tee out.txt

grep '@tag_name_host0' out.txt
grep '@tag_environment_test' out.txt
grep '@tag_status_running' out.txt

# keyed group with default value for key's value empty (list)
ansible-inventory -i tag_inventory.yml -i keyed_group_list_default_value.yml --graph | tee out.txt

grep '@host_db' out.txt
grep '@host_web' out.txt
grep '@host_storage' out.txt

# keyed group with default value for key's value empty (str)
ansible-inventory -i tag_inventory.yml -i keyed_group_str_default_value.yml --graph | tee out.txt

grep '@host_fedora' out.txt


# keyed group with 'trailing_separator' set to 'False' for key's value empty
ansible-inventory -i tag_inventory.yml -i keyed_group_trailing_separator.yml --graph | tee out.txt

grep '@tag_name_host0' out.txt
grep '@tag_environment_test' out.txt
grep '@tag_status' out.txt


# test using use_vars_plugins
ansible-inventory -i invs/1/one.yml -i invs/2/constructed.yml --graph | tee out.txt

grep '@c_lola' out.txt
grep '@c_group4testing' out.txt

# Testing the priority
ansible-inventory -i invs/3/priority_inventory.yml -i invs/3/keyed_group_str_default_value_with_priority.yml --list | tee out.txt

# If we expect the variables to be resolved lexicographically, ('c' would override 'b', which would override 'a')
# then we would expect c_static_group_priority_1 to take precedence.
# However, setting the priorities here is what we're testing, and is indicated in the names of the groups.
#
# If you comment out the priorities of the keyed groups, all of the below will return c_static_group_priority_1

# override_priority_1 is ONLY set in c_static_group_priority_1 - so it should not get overridden by any other group
grep '"override_priority_1": "c_static_group_priority_1"' out.txt
# override_priority_2 is set in both c_static_group_priority_1 and b_keyed_group_priority_2 which (as advertised) has a priority
# of 2, which should override c_static_group_priority_1. This means that the value from b_keyed_group_priority_2 should return.
grep '"override_priority_2": "b_keyed_group_priority_2"' out.txt
# override_priority_3 is set in all the groups, which means the group with the highest priority set should win.
# Lexicographically, this would otherwise be c_static_group_priority_1. However, since we set the priority of
# a_keyed_group_priority_3 to 3, we will expect it to override the other two groups, and return its variable.
# Note that a_keyed_group_priority_3 has its priority set with a conditional, so here we are testing our ability
# to set this priority with a variable, including the `ansible_keyed_group_name` variable that we expose.
grep '"override_priority_3": "a_keyed_group_priority_3"' out.txt
