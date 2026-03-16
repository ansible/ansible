#!/usr/bin/env bash

set -eu

source ../collection/setup.sh

set -x

ansible-test sanity --test action-plugin-docs --color "${@}"
