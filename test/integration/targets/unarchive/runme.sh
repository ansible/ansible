#!/usr/bin/env bash

set -eux

ansible-playbook -i ../../inventory runme.yml -v "$@"

# https://github.com/ansible/ansible/issues/80710
ANSIBLE_REMOTE_TMP=./ansible ansible-playbook -i ../../inventory test_relative_tmp_dir.yml -v "$@"
