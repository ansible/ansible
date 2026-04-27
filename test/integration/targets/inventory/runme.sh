#!/usr/bin/env bash

set -eux

empty_limit_file="$(mktemp)"
touch "${empty_limit_file}"

tmpdir="$(mktemp -d)"

cleanup() {
    if [[ -f "${empty_limit_file}" ]]; then
            rm -rf "${empty_limit_file}"
    fi
    rm -rf "$tmpdir"
}

trap 'cleanup' EXIT

# https://github.com/ansible/ansible/issues/52152
# Ensure that non-matching limit causes failure with rc 1
if ansible-playbook -i ../../inventory --limit foo playbook.yml; then
    echo "Non-matching limit should cause failure"
    exit 1
fi

# Ensure that non-existing limit file causes failure with rc 1
if ansible-playbook -i ../../inventory --limit @foo playbook.yml; then
    echo "Non-existing limit file should cause failure"
    exit 1
fi

if ! ansible-playbook -i ../../inventory --limit @"$tmpdir" playbook.yml 2>&1 | grep 'must be a file'; then
    echo "Using a directory as a limit file should throw proper AnsibleError"
    exit 1
fi

# Ensure that empty limit file does not cause IndexError #59695
ansible-playbook -i ../../inventory --limit @"${empty_limit_file}" playbook.yml

ansible-playbook -i ../../inventory "$@" strategy.yml
ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=always ansible-playbook -i ../../inventory "$@" strategy.yml
ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=never ansible-playbook -i ../../inventory "$@" strategy.yml

# test extra vars
ansible-inventory -i testhost, -i ./extra_vars_constructed.yml --list -e 'from_extras=hey ' "$@"|grep ': "hellohey"'

# test host vars from previous inventory sources
ansible-inventory -i ./inv_with_host_vars.yml -i ./host_vars_constructed.yml --graph "$@" | tee out.txt
if [[ "$(grep out.txt -ce '.*host_var[1|2]_defined')" != 2 ]]; then
    cat out.txt
    echo "Expected groups host_var1_defined and host_var2_defined to both exist"
    exit 1
fi

# Do not fail when all inventories fail to parse.
# Do not fail when any inventory fails to parse.
ANSIBLE_INVENTORY_UNPARSED_FAILED=False ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED=False ansible -m ping localhost -i /idontexist "$@"

# Fail when all inventories fail to parse.
# Do not fail when just one inventory fails to parse.
if ANSIBLE_INVENTORY_UNPARSED_FAILED=True ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED=False ansible -m ping localhost -i /idontexist; then
    echo "All inventories failed/did not exist, should cause failure"
    echo "ran with: ANSIBLE_INVENTORY_UNPARSED_FAILED=True ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED=False"
    exit 1
fi

# Same as above but ensuring no failure we *only* fail when all inventories fail to parse.
# Fail when all inventories fail to parse.
# Do not fail when just one inventory fails to parse.
ANSIBLE_INVENTORY_UNPARSED_FAILED=True ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED=False ansible -m ping localhost -i /idontexist -i ../../inventory "$@"
# Fail when all inventories fail to parse.
# Do not fail when just one inventory fails to parse.

# Fail when any inventories fail to parse.
if ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED=True ansible -m ping localhost -i /idontexist -i ../../inventory; then
    echo "One inventory failed/did not exist, should NOT cause failure"
    echo "ran with: ANSIBLE_INVENTORY_UNPARSED_FAILED=True ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED=False"
    exit 1
fi

# Test parsing an empty config
set +e
ANSIBLE_INVENTORY_UNPARSED_FAILED=True ANSIBLE_INVENTORY_ENABLED=constructed ansible-inventory -i ./test_empty.yml --list "$@"
rc_failed_inventory="$?"
set -e
if [[ "$rc_failed_inventory" != 1 ]]; then
    echo "Config was empty so inventory was not parsed, should cause failure"
    exit 1
fi

# Ensure we don't throw when an empty directory is used as inventory
ansible-playbook -i "$tmpdir" playbook.yml

# Ensure we can use a directory of inventories
cp ../../inventory "$tmpdir"
ansible-playbook -i "$tmpdir" playbook.yml

# ... even if it contains another empty directory
mkdir "$tmpdir/empty"
ansible-playbook -i "$tmpdir" playbook.yml

if ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED=True ansible -m ping localhost -i "$tmpdir"; then
    echo "Empty directory should cause failure when ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED=True"
    exit 1
fi

# ensure we don't traceback on inventory due to variables with int as key
ansible-inventory  -i inv_with_int.yml --list "$@"


# test in subshell relative paths work mid play for extra vars in inventory refresh
{
	cd 1/2
	ansible-playbook -e @../vars.yml -i 'web_host.example.com,' -i inventory.yml 3/extra_vars_relative.yml "$@"
}
