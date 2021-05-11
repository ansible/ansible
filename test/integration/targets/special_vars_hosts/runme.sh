#!/usr/bin/env bash

set -eux

ansible-playbook -i ./inventory playbook.yml "$@" | tee out.txt
grep 'unreachable=2' out.txt
grep 'failed=2' out.txt
