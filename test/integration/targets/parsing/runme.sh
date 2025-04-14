#!/usr/bin/env bash

set -eux

ansible-playbook parsing.yml -i ../../inventory "$@" -e "output_dir=${OUTPUT_DIR}"
ansible-playbook good_parsing.yml -i ../../inventory "$@"

# test that we don't inject _raw_params with invalid extra vars
[ "$(ansible -m debug testhost -i ../../inventory -e 'bad var as string' 2>&1 |grep -c 'Invalid extra vars data supplied')" -gt "0" ]
# test that we don't inject _raw_params with extra data
[ "$(ansible -m debug testhost -i ../../inventory -e 'valid=var inkvalidstring' 2>&1 |grep -c 'Ignoring unparsable data')" -gt "0" ]

# but we can still create normally
ansible-playbook valid_extras.yml -i ../../inventory -e 'valid="as string"' "$@"
