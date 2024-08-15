#!/usr/bin/env bash

set -eux

source virtualenv.sh

pip install pexpect==4.9.0

./test_run_once.py -i inventory "$@"
