#!/usr/bin/env bash
set -eux

ansible-playbook --vault-password-file pw main.yml -i ../../inventory -v "$@"
