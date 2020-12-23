#!/usr/bin/env bash

set -eux

# Test lookup plugin option deprecation
ANSIBLE_DEPRECATION_WARNINGS=true ansible-playbook test.yml 2>&1 | tee out.txt

grep "deprecated_option option, this option should not be" out.txt
grep "used, use no option instead instead. This feature will be removed in version" out.txt
grep -E "(0;35m|^)10.0.0. Deprecation" out.txt

grep "deprecated_option option, this option should not be" out.txt
grep "used, use no option instead instead. This feature will be removed from" out.txt
grep "foo_ns.bar in version 1.0.0. Deprecation" out.txt
