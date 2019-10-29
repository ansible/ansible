#!/usr/bin/env bash

set -eux

ansible-playbook bad_parsing.yml  -i ../../inventory -vvv "$@" --tags prepare,common,scenario5
ansible-playbook good_parsing.yml -i ../../inventory -v "$@"
