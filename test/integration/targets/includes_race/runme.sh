#!/usr/bin/env bash

set -eux

ansible-playbook test_includes_race.yml -i inventory -v "$@"
