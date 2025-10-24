#!/usr/bin/env bash

set -eux

ansible-playbook verify.yml -i generator.yml "${@}"

ANSIBLE_INVENTORY_USE_EXTRA_VARS=True ansible-inventory -i extra_vars_generator.yml --graph -e "region=pune" > out.txt

grep 'pune_web' out.txt
grep 'pune_db' out.txt
