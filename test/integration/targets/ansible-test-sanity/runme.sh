#!/usr/bin/env bash

source ../collection/setup.sh

set -x

ansible-test sanity --color --truncate 0 "${@}"
