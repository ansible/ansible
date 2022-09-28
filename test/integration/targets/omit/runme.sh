#!/usr/bin/env bash

set -eux

ansible-playbook 48673.yml 75692.yml  -i ../../inventory -v "$@"
