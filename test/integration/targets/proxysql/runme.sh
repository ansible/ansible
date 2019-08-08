#!/usr/bin/env bash
# Usage: source ../setup_paramiko/setup.sh

set -eux

source virtualenv.sh  # for pip installs, if needed, otherwise unused
ansible-playbook -i ../proxysql/inventory proxysql.yml "$@"
