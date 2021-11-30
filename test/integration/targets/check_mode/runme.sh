#!/usr/bin/env bash

set -eux

ansible-playbook check_mode.yml -i ../../inventory -v --check "$@"
ansible-playbook check_mode-on-cli.yml -i ../../inventory -v --check "$@"
ansible-playbook check_mode-not-on-cli.yml -i ../../inventory -v "$@"
