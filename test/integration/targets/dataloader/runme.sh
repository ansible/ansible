#!/usr/bin/env bash

set -eux

# check if we get proper json error
ANSIBLE_DISPLAY_TRACEBACK=always ansible-playbook -i ../../inventory attempt_to_load_invalid_json.yml "$@" 2>&1 | grep 'parsing failed: Did not find expected <document start>'

echo PASS
