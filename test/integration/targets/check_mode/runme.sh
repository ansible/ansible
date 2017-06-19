#!/usr/bin/env bash

set -eux

ansible-playbook check_mode.yml -i ../../inventory -v --check "$@"
