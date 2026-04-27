#!/usr/bin/env bash

set -eux

ansible-playbook runme.yml -i inventory -v "$@"
