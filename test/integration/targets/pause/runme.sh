#!/usr/bin/env bash

set -eux

pip install pexpect
python test-pause.py -i ../../inventory "$@"
