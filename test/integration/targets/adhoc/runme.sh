#!/usr/bin/env bash

set -eux

# run type tests
ansible -a 'sleep 20' --task-timeout 5 localhost |grep 'The command action failed to execute in the expected time frame (5) and was terminated'

# -a parsing with json
ansible --task-timeout 5 localhost -m command -a '{"cmd": "whoami"}' | grep 'rc=0'
