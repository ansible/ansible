#!/usr/bin/env bash

set -eux
set -o pipefail

# http://unix.stackexchange.com/questions/30091/fix-or-alternative-for-mktemp-in-os-x
temp_dir=$(shell mktemp -d 2>/dev/null || mktemp -d -t 'ansible-testing-XXXXXXXXXX')
trap 'rm -rf "${temp_dir}"' EXIT

repo_dir="${temp_dir}/repo"
pull_dir="${temp_dir}/pull"
temp_log="${temp_dir}/pull.log"

ansible-playbook setup.yml -i ../../inventory

cleanup="$(pwd)/cleanup.yml"

trap 'ansible-playbook "${cleanup}" -i ../../inventory' EXIT

cp -av "pull-integration-test" "${repo_dir}"
cd "${repo_dir}"
(
    git init
    git config user.email "ansible@ansible.com"
    git config user.name  "Ansible Test Runner"
    git add .
    git commit -m "Initial commit."
)

function pass_tests {
	# test for https://github.com/ansible/ansible/issues/13688
	if ! grep MAGICKEYWORD "${temp_log}"; then
	    cat "${temp_log}"
	    echo "Missing MAGICKEYWORD in output."
	    exit 1
	fi

	# test for https://github.com/ansible/ansible/issues/13681
	if grep -E '127\.0\.0\.1.*ok' "${temp_log}"; then
	    cat "${temp_log}"
	    echo "Found host 127.0.0.1 in output. Only localhost should be present."
	    exit 1
	fi
	# make sure one host was run
	if ! grep -E 'localhost.*ok' "${temp_log}"; then
	    cat "${temp_log}"
	    echo "Did not find host localhost in output."
	    exit 1
	fi
}

export ANSIBLE_INVENTORY
export ANSIBLE_HOST_PATTERN_MISMATCH

unset ANSIBLE_INVENTORY
unset ANSIBLE_HOST_PATTERN_MISMATCH

ANSIBLE_CONFIG='' ansible-pull -d "${pull_dir}" -U "${repo_dir}" "$@" | tee "${temp_log}"

pass_tests

# ensure complex extra vars work
PASSWORD='test'
USER=${USER:-'broken_docker'}
JSON_EXTRA_ARGS='{"docker_registries_login": [{ "docker_password": "'"${PASSWORD}"'", "docker_username": "'"${USER}"'", "docker_registry_url":"repository-manager.company.com:5001"}], "docker_registries_logout": [{ "docker_password": "'"${PASSWORD}"'", "docker_username": "'"${USER}"'", "docker_registry_url":"repository-manager.company.com:5001"}] }'

ANSIBLE_CONFIG='' ansible-pull -d "${pull_dir}" -U "${repo_dir}" -e "${JSON_EXTRA_ARGS}" "$@" --tags untagged,test_ev | tee "${temp_log}"

pass_tests
