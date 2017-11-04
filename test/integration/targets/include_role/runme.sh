#!/usr/bin/env bash
set -eux
ansible-playbook -i../../inventory include_role.yml -v
