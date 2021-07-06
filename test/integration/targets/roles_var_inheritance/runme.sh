#!/usr/bin/env bash

set -eux

ansible-playbook -i ../../inventory play.yml "$@" | tee out.txt

test "$(grep out.txt -ce '"nested_var": "A"')" == 1
test "$(grep out.txt -ce '"nested_var": "B"')" == 1
test "$(grep out.txt -ce '"var_precedence": "dependency"')" == 2
