#!/usr/bin/env bash

set -eux

# we are looking to verify the callback for v2_retry_runner gets a correct task name, include
# if the value needs templating based on results of previous tasks
OUTFILE="callback_output_copy.out"
trap 'rm -rf "${OUTFILE}"' EXIT

# test task retry name
EXPECTED_REGEX="^.*TASK.*18236 callback task template fix OUTPUT 2"
ansible-playbook "$@" -i ../../inventory task_name.yml | tee "${OUTFILE}"
echo "Grepping for ${EXPECTED_REGEX} in stdout."
grep -e "${EXPECTED_REGEX}" "${OUTFILE}"

# test connection tracking
EXPECTED_CONNECTION='{"testhost":{"ssh":4}}'
OUTPUT_TAIL=$(tail -n5 ${OUTFILE} | tr -d '[:space:]')
[ "${EXPECTED_CONNECTION}" == "${OUTPUT_TAIL}" ]
echo $?
