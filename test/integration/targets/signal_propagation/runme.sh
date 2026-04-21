#!/usr/bin/env bash

set -x

echo "Test signal propagation with isolated and non-isolated workers"
for isolation in 0 1
do
  ANSIBLE_WORKER_SESSION_ISOLATION=$isolation ../test_utils/scripts/timeout.py -s SIGINT 3 -- \
      ansible all -i inventory -m debug -a 'msg={{lookup("pipe", "sleep 33")}}' -f 10
  if [[ "$?" != "124" ]]; then
      echo "Process was not terminated due to timeout"
      exit 1
  fi

  # a short sleep to let processes die
  sleep 2

  sleeps="$(pgrep -alf 'sleep\ 33')"
  rc="$?"
  if [[ "$rc" == "0" ]]; then
      echo "Found lingering processes:"
      echo "$sleeps"
      exit 1
  fi
done
