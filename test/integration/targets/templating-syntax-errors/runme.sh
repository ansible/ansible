#!/usr/bin/env bash

set -eux

ansible-playbook template-file.yml "${@}" | tee template-file.out

echo "Verifying contents of error reports ..."

# verify the template-file error report is correct
grep 'template-file.j2:5' template-file.out
grep '5 {% sorry' template-file.out

echo "PASS"
