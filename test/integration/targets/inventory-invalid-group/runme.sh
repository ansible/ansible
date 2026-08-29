#!/usr/bin/env bash

set -eux
set -o pipefail

command=(ansible-playbook -v -i inventory.ini test.yml)
 never='Invalid characters were found in group names but not replaced'
always='Invalid characters were found in group names and automatically'

ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=never    "${command[@]}" -l "local-" 2>&1 | grep -c  -e "${never}"
ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=always   "${command[@]}" -l "local_" 2>&1 | grep -c  -e "${always}"
ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=ignore   "${command[@]}" -l "local-" 2>&1 | grep -cv -e "${never}" -e "${always}"
ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=silently "${command[@]}" -l "local_" 2>&1 | grep -cv -e "${never}" -e "${always}"
