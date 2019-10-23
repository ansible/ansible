#!/usr/bin/env bash

# http://www.linuxcommand.org/lc3_man_pages/seth.html
# set -eux

if [[ -f /usr/local/bin/hiera ]]
then
    export ANSIBLE_HIERA_BIN=/usr/local/bin/hiera
fi

ANSIBLE_HIERA_CFG="$(pwd)/hiera.yaml"
export ANSIBLE_HIERA_CFG

ANSIBLE_LOOKUP_PLUGINS="$(pwd)/../../../../lib/ansible/plugins/lookup"
export ANSIBLE_LOOKUP_PLUGINS

ansible-playbook main.yml -v "$@"
