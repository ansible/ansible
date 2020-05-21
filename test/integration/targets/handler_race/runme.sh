#!/usr/bin/env bash

set -eux

ansible-playbook test_handler_race.yml -i inventory -v "$@"

