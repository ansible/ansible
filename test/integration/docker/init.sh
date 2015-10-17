#!/bin/bash
set -ev

cd /ansible/
source ./hacking/env-setup
cd /ansible/test/integration

#export TEST_FLAGS="-vvvvv --skip-tags \"test_github_private_key\""
export CREDENTIALS_FILE=""
make non_destructive && make destructive

