#!/usr/bin/env bash

set -eux
set -o pipefail

# http://unix.stackexchange.com/questions/30091/fix-or-alternative-for-mktemp-in-os-x
temp_dir=$(shell mktemp -d 2>/dev/null || mktemp -d -t 'ansible-testing-XXXXXXXXXX')
trap 'rm -rf "${temp_dir}"' EXIT

repo_dir="${temp_dir}/repo"
pull_dir="${temp_dir}/pull"
temp_log="${temp_dir}/pull.log"

cp -av "pull-integration-test" "${repo_dir}"
cd "${repo_dir}"
(
    git init
    git config user.email "ansible@ansible.com"
    git config user.name  "Ansible Test Runner"
    git add .
    git commit -m "Initial commit."
)

ANSIBLE_CONFIG='' ansible-pull -d "${pull_dir}" -U "${repo_dir}" "$@" | tee "${temp_log}"

# test for https://github.com/ansible/ansible/issues/13688
if ! grep MAGICKEYWORD "${temp_log}"; then
    echo "Missing MAGICKEYWORD in output."
    exit 1
fi

# test for https://github.com/ansible/ansible/issues/13681
if egrep '127\.0\.0\.1.*ok' "${temp_log}"; then
    echo "Found host 127.0.0.1 in output. Only localhost should be present."
    exit 1
fi
# make sure one host was run
if ! egrep 'localhost.*ok' "${temp_log}"; then
    echo "Did not find host localhost in output."
    exit 1
fi
