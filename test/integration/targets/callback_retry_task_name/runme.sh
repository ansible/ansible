#!/usr/bin/env bash

set -eux

# we are looking to verify the callback for v2_retry_runner gets a correct task name, include
# if the value needs templating based on results of previous tasks
OUTFILE="callback_retry_task_name.out"
trap 'rm -rf "${OUTFILE}"' EXIT

EXPECTED_REGEX="^.*TASK.*18236 callback task template fix OUTPUT 2"
ansible-playbook "$@" -i ../../inventory test.yml | tee "${OUTFILE}"
echo "Grepping for ${EXPECTED_REGEX} in stdout."
grep -e "${EXPECTED_REGEX}" "${OUTFILE}"
