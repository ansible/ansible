#!/usr/bin/env bash

set -eux

# run play, should create log and dir if needed
ansible-playbook ping_log.yml -v "$@"
[ -f logit/localhost ]

# now force it to fail
chmod a-rx logit
ansible-playbook ping_log.yml -v "$@" 2>&1| grep 'Failure using method (v2_runner_on_ok) in callback plugin'
[ ! -f logit/localhost ]
