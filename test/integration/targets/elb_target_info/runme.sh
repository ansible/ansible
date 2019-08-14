#!/usr/bin/env bash

set -eux

ansible-playbook -i ../../inventory -v playbooks/full_test.yml "$@"
