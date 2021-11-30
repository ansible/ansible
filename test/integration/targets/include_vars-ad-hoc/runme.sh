#!/usr/bin/env bash

set -eux

ansible testhost -i ../../inventory -m include_vars -a 'dir/inc.yml' "$@"
ansible testhost -i ../../inventory -m include_vars -a 'dir=dir' "$@"
