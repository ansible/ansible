#!/usr/bin/env bash

set -eux

ansible-playbook *.yml -i ../../inventory -v "$@"
