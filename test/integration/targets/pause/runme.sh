#!/usr/bin/env bash

set -eux

ansible-playbook test-pause.yml -i ../../inventory "$@"

pip install pexpect
python test-pause.py -i ../../inventory "$@"
