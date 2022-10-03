#!/usr/bin/env bash

set -eux

ANSIBLE_ROLES_PATH=../ ansible-playbook 48673.yml 75692.yml -i ../../inventory -v "$@"
