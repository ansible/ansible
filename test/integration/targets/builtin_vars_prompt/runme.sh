#!/usr/bin/env bash

set -eux

source virtualenv.sh

pip install pexpect==4.9.0 passlib==1.7.4

# Interactively test vars_prompt
python test-vars_prompt.py -i ../../inventory "$@"
