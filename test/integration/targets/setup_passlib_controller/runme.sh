#!/usr/bin/env bash

set -eux

# Requirements have to be installed prior to running ansible-playbook
# because plugins and requirements are loaded before the task runs
python -m pip install passlib
