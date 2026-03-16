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

# check variables are interpolated in 'started'
UNTEMPLATED_STARTED="^.*\[started .*{{.*}}.*$"
echo "Checking we dont have untemplated started in stdout."
if grep -e "${UNTEMPLATED_STARTED}" "${OUTFILE}"; then
  exit 1
fi

# test connection tracking
ANSIBLE_CALLBACKS_ENABLED=track_connections ansible-playbook "$@" -i ../../inventory connection_name.yml | tee "${OUTFILE}"
grep "FOUND EXPECTED EVENTS" "${OUTFILE}"

# test configuring display_skipped_hosts using --extra-vars
hide_skipped="$(ansible-playbook skip_hosts.yml -v --extra-vars @./callback_vars.yml "$@")"
if [[ "$hide_skipped" == *skip_reason* ]]; then
  echo "Failed to configure display_skipped_hosts (false)"
  exit 1
fi
include_skipped="$(ansible-playbook skip_hosts.yml -v --extra-vars @./callback_vars.yml --extra-vars indirect_extra=true "$@")"
if [[ "$include_skipped" != *skip_reason* ]]; then
    echo "Failed to configure display_skipped_hosts (true)"
    exit 1
fi
include_skipped="$(ansible-playbook skip_hosts.yml -v --extra-vars @./callback_vars.yml --extra-vars indirect_extra='{{ omit }}' "$@")"
if [[ "$include_skipped" != *skip_reason* ]]; then
    echo "Failed to omit display_skipped_hosts (default true)"
    exit 1
fi
