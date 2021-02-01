#!/usr/bin/env bash

set -eux

ansible-playbook include_role_dynamic.yml -i inventory "$@"
