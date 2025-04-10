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

function change_repo {
    cd "${repo_dir}"
    date > forced_change
    git add forced_change
    git commit -m "forced changed"
    cd -
}

function no_change_tests {
    # test for https://github.com/ansible/ansible/issues/13688
    if grep MAGICKEYWORD "${temp_log}"; then
        cat "${temp_log}"
        echo "Ran the playbook, found MAGICKEYWORD in output."
        exit 1
    fi
}

function pass_tests {
	# test for https://github.com/ansible/ansible/issues/13688
	if ! grep MAGICKEYWORD "${temp_log}"; then
	    cat "${temp_log}"
	    echo "Missing MAGICKEYWORD in output."
	    exit 1
	fi

	# test for https://github.com/ansible/ansible/issues/13681
	# match play default output stats, was matching limit + docker
	if grep -E '127\.0\.0\.1\s*: ok=' "${temp_log}"; then
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

function pass_tests_multi {
	# test for https://github.com/ansible/ansible/issues/72708
	if ! grep 'test multi_play_1' "${temp_log}"; then
		cat "${temp_log}"
		echo "Did not run multiple playbooks"
		exit 1
	fi
	if ! grep 'test multi_play_2' "${temp_log}"; then
		cat "${temp_log}"
		echo "Did not run multiple playbooks"
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

ANSIBLE_CONFIG='' ansible-pull -d "${pull_dir}" -U "${repo_dir}" "$@" multi_play_1.yml multi_play_2.yml | tee "${temp_log}"

pass_tests_multi

ANSIBLE_CONFIG='' ansible-pull -d "${pull_dir}" -U "${repo_dir}" conn_secret.yml --connection-password-file "${repo_dir}/secret_connection_password" "$@"

# fail if we try do delete /var/tmp
ANSIBLE_CONFIG='' ansible-pull -d var/tmp -U "${repo_dir}" --purge "$@"

# test flushing the fact cache
export ANSIBLE_CACHE_PLUGIN=jsonfile ANSIBLE_CACHE_PLUGIN_CONNECTION=./
ansible-pull -d "${pull_dir}" -U "${repo_dir}" "$@" gather_facts.yml
ansible-pull -d "${pull_dir}" -U "${repo_dir}" --flush-cache "$@" test_empty_facts.yml
unset ANSIBLE_CACHE_PLUGIN ANSIBLE_CACHE_PLUGIN_CONNECTION

#### CHACHCHCHANGES!
echo 'setup for change detection'
ORIG_CONFIG="${ANSIBLE_CONFIG}"
unset ANSIBLE_CONFIG

echo 'test no run on no changes'
ansible-pull -d "${pull_dir}" -U "${repo_dir}" --only-if-changed "$@" | tee "${temp_log}"
no_change_tests

echo 'test run on changes'
change_repo
ansible-pull -d "${pull_dir}" -U "${repo_dir}" --only-if-changed "$@" | tee "${temp_log}"
pass_tests

# test changed with non yaml result format, ensures we ignore callback or format changes for adhoc/change detection
echo 'test no run on no changes, yaml result format'
ANSIBLE_CALLBACK_RESULT_FORMAT='yaml' ansible-pull -d "${pull_dir}" -U "${repo_dir}" --only-if-changed "$@" | tee "${temp_log}"
no_change_tests

echo 'test run on changes, yaml result format'
change_repo
ANSIBLE_CALLBACK_RESULT_FORMAT='yaml' ansible-pull -d "${pull_dir}" -U "${repo_dir}" --only-if-changed "$@" | tee "${temp_log}"
pass_tests

if [ "${ORIG_CONFIG}" != "" ]; then
  export ANSIBLE_CONFIG="${ORIG_CONFIG}"
fi
