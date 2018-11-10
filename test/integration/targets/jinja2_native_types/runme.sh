#!/usr/bin/env bash

set -eux

ANSIBLE_JINJA2_NATIVE=1 ansible-playbook -i inventory.jinja2_native_types runtests.yml -v "$@"
