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

version_info="$(svn --version -q)"
version=( ${version_info//./ } )
expected_min='1.10.0'
min_secure_version=( ${expected_min//./ })
secure=1

if [[ ${version[0]} -lt ${min_secure_version[0]} ]]; then
    secure=0
elif [[ ${version[0]} -eq ${min_secure_version[0]} ]]; then
    if [[ ${version[1]} -lt ${min_secure_version[1]} ]]; then
        secure=0
    elif [[ ${version[1]} -eq ${min_secure_version[1]} ]]; then
        if [[ ${version[2]} -lt ${min_secure_version[2]} ]]; then
	    secure=0
	fi
    fi
fi

if [[ "$secure" -eq 0 ]] && [[ "$(grep -c 'To securely pass credentials, upgrade svn to version 1.10.0' out.txt)" -eq 1 ]]; then
    echo "Found the expected warning"
elif [[ "$secure" -eq 0 ]]; then
    echo "Expected a warning"
    exit 1
fi
