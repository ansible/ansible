#!/usr/bin/env bash
W=$(cd "$(dirname "$0")" && pwd)
export ANSIBLE_ROLES_PATH="$W/nested:$W/roles"
set -eux
ansible-playbook -i../../inventory nested.yml -v
