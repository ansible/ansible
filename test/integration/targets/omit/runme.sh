#!/usr/bin/env bash

set -eux

ansible-playbook 48673.yml -i ../../inventory -v "$@"
