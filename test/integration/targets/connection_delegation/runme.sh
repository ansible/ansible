#!/usr/bin/env bash

set -ux

sshpass -p my_password ansible-playbook -i inventory.ini test.yml -k "$@"
