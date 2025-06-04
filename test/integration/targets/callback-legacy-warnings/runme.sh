#!/usr/bin/env bash

set -eux

ANSIBLE_STDOUT_CALLBACK=legacy_warning_display ansible-playbook test.yml "${@}"
