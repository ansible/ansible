#!/usr/bin/env bash

set -ux
export ANSIBLE_ROLES_PATH=../

is_timeout() {
    rv=$?
    if [ "$rv" == "124" ]; then
        echo "***hang detected, this likely means the strategy never received a result for the task***"
    fi
    exit $rv
}

trap "is_timeout" EXIT

../test_utils/scripts/timeout.py -- 10 ansible-playbook -i ../../inventory runme.yml -v "$@"
