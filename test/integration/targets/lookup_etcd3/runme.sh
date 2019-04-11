#!/usr/bin/env bash

if python -c "help('modules')" | grep -q sysconfig; then

set -eux

source virtualenv.sh

# Requirements have to be installed prior to running ansible-playbook
# because plugins and requirements are loaded before the task runs
pip install passlib
pip install etcd3

ANSIBLE_ROLES_PATH=../ ansible-playbook lookup_etcd3.yml -i ../../inventory -e @../../integration_config.yml "$@"

fi
