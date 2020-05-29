#!/usr/bin/env bash

set -eux
ansible-playbook test.yml -i inventory "$@"

(
unset ANSIBLE_PLAYBOOK_DIR
cd "$(dirname "$0")"

# test module docs, skip header since its abs path and that changes
current_out="$(ansible-doc --playbook-dir ./ fakemodule|grep -v FAKEMODULE)"
expected_out="$(grep -v FAKEMODULE fakemodule.output)"
test "$current_out" == "$expected_out"
)
