#!/usr/bin/env bash

set -ux
set +e

export ANSIBLE_INVENTORY_SAFE_PROCESSING=True

ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED=yes ansible-inventory -i bad_source --list

# Failing to parse a source with ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED enabled should be fatal
if [[ $? -ne 1 ]]; then
    exit 1
fi

set -e

export ANSIBLE_INVENTORY_UNPARSED_FAILED=yes

# Only warn about restoring inventory if the source fails after modifying inventory
ansible-inventory -i good_source -i bad_source_fails_immediately --list 2>&1 | tee out.txt
if [[ "$(grep -c out.txt -e 'restoring inventory')" -ne 0 ]] ; then
    echo "Got a warning for an inventory source that should not have partially modified inventory"
    exit 1
fi

# Ensure that a warning is given when inventory is restored from incomplete modifications
ansible-inventory -i good_source -i good_source -i bad_source --graph 2>&1 | tee out.txt
if [[ "$(grep -c out.txt -e 'restoring inventory')" -ne 1 ]] ; then
    echo "Did not get warning when an inventory source was partially parsed"
    exit 1
fi

ansible-inventory -i good_source -i good_source -i bad_source --graph | tee out.txt

# Inventory should contain no groups or hosts from the failed source
if [[ "$(grep -c out.txt -e 'bad_source_')" -ne 0 ]] ; then
    echo "Found a group or host from the bad inventory source"
    exit 1
fi

# All groups and hosts from the good source should be present (and not duplicated)
if [[ "$(grep -c out.txt -e 'good_source_group0')" -ne 1 ]]
   [[ "$(grep -c out.txt -e 'good_source_group1')" -ne 1 ]] ; then
    echo "Missing a group from the good inventory source"
    exit 1
elif [[ "$(grep -c out.txt -e 'good_source_host0')" -ne 1 ]] ; then
    echo "Missing a host from the good inventory source"
    exit 1
fi

ansible-inventory -i good_source -i bad_source --list | tee out.txt

# Inventory should contain no variables from the bad source
if [[ "$(grep -c out.txt -e 'bad_source_')" -ne 0 ]] ; then
    echo "Found a variable from the bad inventory source"
    exit 1
fi

# All variables from the good source should be in inventory
if [[ "$(grep -c out.txt -e 'good_source_hostvar0')" -ne 1 ]]
   [[ "$(grep -c out.txt -e 'good_source_groupvar0')" -ne 1 ]]
   [[ "$(grep -c out.txt -e 'good_source_groupvar1')" -ne 1 ]]
   [[ "$(grep -c out.txt -e 'good_source_groupvar2')" -ne 1 ]] ; then
    echo "Missing a variable from the good inventory source"
    exit 1
fi
