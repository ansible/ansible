#!/usr/bin/env bash

set -euvx
source virtualenv.sh

ansible-playbook "$@" test.yml