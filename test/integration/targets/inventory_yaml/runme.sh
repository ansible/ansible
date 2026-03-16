#!/usr/bin/env bash

set -eux -o pipefail

# handle empty/commented out group keys correctly https://github.com/ansible/ansible/issues/47254
ANSIBLE_VERBOSITY=0 diff --unified -w <(ansible-inventory -i ./test.yml --list) success.json

ansible-inventory -i ./test_int_hostname.yml --list 2>&1 | grep 'Host pattern 1234 must be a string'
