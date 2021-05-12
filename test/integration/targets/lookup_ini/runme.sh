#!/usr/bin/env bash

set -eux

ansible-playbook test_lookup_properties.yml -i inventory -v "$@"
ansible-playbook test_errors.yml -i inventory -v "$@"
