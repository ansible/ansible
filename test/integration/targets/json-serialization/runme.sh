#!/usr/bin/env bash

set -eux

export ANSIBLE_FORCE_COLOR=0

ANSIBLE_MODULE_STRICT_UTF8_RESPONSE=0 ansible-playbook test.yml "${@}" | grep 'hi ? mom'

ANSIBLE_MODULE_STRICT_UTF8_RESPONSE=1 ansible-playbook test.yml "${@}" 2>&1 | grep "^Refusing to deserialize an invalid UTF8 string value"

echo PASS
