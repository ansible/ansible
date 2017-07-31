#!/usr/bin/env bash

set -eux

ansible-playbook module_utils_test.yml -i ../../inventory -v "$@"
ANSIBLE_MODULE_UTILS=$(pwd)/other_mu_dir ansible-playbook module_utils_envvar.yml -i ../../inventory -v "$@"
