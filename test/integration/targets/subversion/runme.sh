#!/usr/bin/env bash

set -eu

cleanup() {
    echo "Cleanup"
    ansible-playbook runme.yml -e "output_dir=${OUTPUT_DIR}" "$@" --tags cleanup
    echo "Done"
}

trap cleanup INT TERM EXIT

export ANSIBLE_ROLES_PATH=roles/

# Ensure subversion is set up
ansible-playbook runme.yml "$@" -v --tags setup

# Test functionality
ansible-playbook runme.yml "$@" -v --tags tests

# Test a warning is displayed for versions < 1.10.0 when a password is provided
ansible-playbook runme.yml "$@" --tags warnings 2>&1 | tee out.txt

version="$(svn --version -q)"
secure=$(python -c "from distutils.version import LooseVersion; print(LooseVersion('$version') >= LooseVersion('1.10.0'))")

if [[ "${secure}" = "False" ]] && [[ "$(grep -c 'To securely pass credentials, upgrade svn to version 1.10.0' out.txt)" -eq 1 ]]; then
    echo "Found the expected warning"
elif [[ "${secure}" = "False" ]]; then
    echo "Expected a warning"
    exit 1
fi
