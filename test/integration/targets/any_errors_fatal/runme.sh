#!/usr/bin/env bash

set -eux

ansible-playbook -i ../../inventory -e @../../integration_config.yml "$@" always_block.yml | tee out.txt | grep 'any_errors_fatal_always_block_start'

exit $?
