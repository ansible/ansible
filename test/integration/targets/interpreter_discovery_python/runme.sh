#!/usr/bin/env bash

set -eux

ansible-playbook discovery.yml -i ../../inventory "${@}"

# Run with -vvv to see the discovery message. This allows us to verify that discovery actually ran.
ansible-playbook bad-connection.yml -vvv 2>&1 | tee discovery.txt

grep 'Attempting python interpreter discovery.' discovery.txt

out="$(ansible-playbook -i intra_task,inter_task reuse_discovery.yml -vvv "$@")"
[ "$(grep -c "<intra_task> Attempting python interpreter discovery." <<< "$out")" -eq 1 ]
[ "$(grep -c "<inter_task> Attempting python interpreter discovery." <<< "$out")" -eq 1 ]
