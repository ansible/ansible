#!/usr/bin/env bash

set -eux

ANSIBLE_ROLES_PATH=../ ansible-playbook --vault-password-file vault-password runme.yml -i inventory "${@}"
