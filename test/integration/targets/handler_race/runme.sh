#!/usr/bin/env bash

set -eux

ansible-playbook test_handler_race.yml --forks 30 -i inventory -v "$@"