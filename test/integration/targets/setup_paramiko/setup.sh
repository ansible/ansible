#!/usr/bin/env bash
# Usage: source ../setup_paramiko/setup.sh

set -eux

export ANSIBLE_TEST_PREFER_VENV=1
source virtualenv.sh  # for pip installs, if needed, otherwise unused
ANSIBLE_ROLES_PATH=../ ansible-playbook ../setup_paramiko/install.yml -i ../setup_paramiko/inventory "$@"
trap 'ansible-playbook ../setup_paramiko/uninstall.yml -i ../setup_paramiko/inventory "$@"' EXIT
