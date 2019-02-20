#!/usr/bin/env bash

set -eux

ansible-playbook test_filelock.yml -i inventory --forks 100 -v "$@"
ansible-playbook test_filelock_timeout.yml -i inventory -v "$@"
