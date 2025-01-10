#!/usr/bin/env bash

set -eux

ansible-inventory -i generator.yml --graph | tee out.txt

grep 'mumbai_web' out.txt
grep 'mumbai_db' out.txt
grep 'pune_web' out.txt
grep 'pune_db' out.txt

ANSIBLE_INVENTORY_USE_EXTRA_VARS=True ansible-inventory -i extra_vars_generator.yml --graph -e "region=pune"

grep 'pune_web' out.txt
grep 'pune_db' out.txt

ansible-inventory -i generator_parent.yml --graph | tee out.txt

grep 'web_build_runner' out.txt
grep 'api_build_runner' out.txt
grep 'web_launch_runner' out.txt
grep 'api_launch_runner' out.txt
grep '@dev' out.txt
grep '@test' out.txt
grep '@prod' out.txt
