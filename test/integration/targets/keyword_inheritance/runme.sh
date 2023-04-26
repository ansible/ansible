#!/usr/bin/env bash

set -eux

ANSIBLE_ROLES_PATH=../ ansible-playbook -i ../../inventory test.yml "$@"

ANSIBLE_ROLES_PATH=../ ansible-playbook -i ../../inventory dep_keyword_inheritance.yml "$@"
