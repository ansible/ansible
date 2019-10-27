#!/usr/bin/env bash

set -eux

cd ../binary_modules
INVENTORY=../../inventory ./test.sh "$@"
