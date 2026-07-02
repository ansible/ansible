#!/usr/bin/env bash

set -eux -o pipefail

export ANSIBLE_TIMEOUT=1

export ANSIBLE_CONNECTION_PLUGINS=./fake_connectors
# use fake connectors that raise errors at different stages
ansible-playbook test_with_bad_plugins.yml -i inventory -v "$@"
unset ANSIBLE_CONNECTION_PLUGINS

ansible-playbook test_cannot_connect.yml -i inventory -v "$@"

(ansible-playbook test_base_cannot_connect.yml -i inventory -v "$@" || true) | tee out.txt

grep PASSED out.txt

ansible-playbook test_base_loop_cannot_connect.yml -i inventory -v "$@" | tee out.txt

grep 'nonexistent.*unreachable=1' out.txt
grep PASSED out.txt
