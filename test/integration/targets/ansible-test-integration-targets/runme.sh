#!/usr/bin/env bash

test="$(pwd)/test.py"

source ../collection/setup.sh

set -x

"${test}" -v
