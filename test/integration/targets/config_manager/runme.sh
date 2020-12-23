#!/usr/bin/env bash

set -eux

ansible-playbook test.yml 2>&1 | tee out.txt

grep "deprecated_option option, this option should not be" out.txt
grep "used, use no option instead instead." out.txt
