#!/usr/bin/env bash

set -eux

ansible-playbook -i inventory/hosts.yml main.yml  "$@"
