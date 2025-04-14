#!/usr/bin/env bash

set -eux

ANSIBLE_ALLOW_EMBEDDED_TEMPLATES=1 ansible-playbook -i ../../inventory test.yml "${@}"
