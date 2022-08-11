#!/usr/bin/env bash

set -eu

source ../collection/setup.sh

set -x

ansible-test sanity --test ansible-doc --color "${@}"
