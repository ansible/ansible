#!/usr/bin/env bash

# handle empty/commented out group keys correctly https://github.com/ansible/ansible/issues/47254
ANSIBLE_VERBOSITY=0 diff -w <(ansible-inventory -i ./test.yml --list) success.json
