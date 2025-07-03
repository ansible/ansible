#!/usr/bin/env bash

set -eux

ansible-playbook -i ../../inventory play.yml "$@"

ansible-playbook -i ../../inventory output_validation_tests.yml

ansible-playbook -i ../../inventory broken_conditionals.yml

ANSIBLE_ALLOW_BROKEN_CONDITIONALS=1 ANSIBLE_DEPRECATION_WARNINGS=1 ansible-playbook -i ../../inventory broken_conditionals.yml

# DTFIX-FUTURE: capture output and diff against expected deprecation warnings/errors
