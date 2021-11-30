#!/usr/bin/env bash

set -eux

ansible-playbook -v -i inventory.ini test_ansible_become.yml
