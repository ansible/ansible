#!/usr/bin/env bash

set -eux -o pipefail

cleanup() {
    echo "Cleanup"
    ansible-playbook runme.yml -i "${INVENTORY_PATH}" "$@" --tags cleanup
    echo "Done"
}

trap cleanup INT TERM EXIT

export ANSIBLE_ROLES_PATH=roles/

# Ensure subversion is set up
ansible-playbook runme.yml -i "${INVENTORY_PATH}" "$@" -v --tags setup

# Test functionality
ansible-playbook runme.yml -i "${INVENTORY_PATH}" "$@" -v --tags tests

# Test a warning is displayed for versions < 1.10.0 when a password is provided
ansible-playbook runme.yml -i "${INVENTORY_PATH}" "$@" --tags warnings 2>&1 | tee out.txt

version=$(ANSIBLE_FORCE_COLOR=0 ansible -i "${INVENTORY_PATH}" -m shell -a 'svn --version -q' testhost 2>/dev/null | tail -n 1)

echo "svn --version is '${version}'"

secure=$(python -c "from ansible.module_utils.compat.version import LooseVersion; print(LooseVersion('$version') >= LooseVersion('1.10.0'))")

if [[ "${secure}" = "False" ]] && [[ "$(grep -c 'To securely pass credentials, upgrade svn to version 1.10.0' out.txt)" -eq 1 ]]; then
    echo "Found the expected warning"
elif [[ "${secure}" = "False" ]]; then
    echo "Expected a warning"
    exit 1
fi
