#!/usr/bin/env bash

set -eux

ansible-playbook test_include_file_noop.yml -i inventory "$@"

ansible-playbook task_action_templating.yml -i inventory "$@"

ansible-playbook task_templated_run_once.yml -i inventory "$@"

ansible-playbook test_run_once_rescue.yml -i inventory "$@" | tee out.txt

# test number of actual tasks executed
test "$(grep -c '"task [1-4] testhost"' out.txt)" == 4
test "$(grep -c '"task [1-4] testhost2"' out.txt)" == 1
grep '"task 4 testhost2"' out.txt

# test play recap agrees
grep 'testhost.*ok=2.*rescued=2' out.txt
grep 'testhost2.*ok=1.*rescued=2' out.txt
