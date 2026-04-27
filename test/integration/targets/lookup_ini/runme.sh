#!/usr/bin/env bash

set -eux

ansible-playbook test_ini.yml -i inventory -v "$@"
