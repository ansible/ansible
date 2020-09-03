#!/usr/bin/env bash

set -eux

export ANSIBLE_JINJA2_NATIVE=1
ansible-playbook 46169.yml -v "$@"
unset ANSIBLE_JINJA2_NATIVE
