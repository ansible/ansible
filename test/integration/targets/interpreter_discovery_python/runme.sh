#!/usr/bin/env bash

set -eux

ansible-playbook discovery.yml -i ../../inventory "${@}"

# Run with -vvv to see the discovery message. This allows us to verify that discovery actually ran.
ansible-playbook bad-connection.yml -vvv 2>&1 | tee discovery.txt

grep 'Attempting python interpreter discovery.' discovery.txt
