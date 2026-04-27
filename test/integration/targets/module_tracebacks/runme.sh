#!/usr/bin/env bash

set -eux

ansible-playbook traceback.yml -i inventory "$@"

ANSIBLE_DISPLAY_TRACEBACK=error ansible-playbook traceback.yml -i inventory "$@"
