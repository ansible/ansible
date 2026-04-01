#!/usr/bin/env bash

set -eux

ansible-playbook test_includes_race.yml --forks 30 -i inventory -v "$@"
