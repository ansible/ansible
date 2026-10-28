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

echo "Test a SIGINT whose KeyboardInterrupt CPython discards: in a lock's at-fork callback while a worker is forked, and in a finalizer"
for where in fork finalizer
do
  ANSIBLE_CALLBACKS_ENABLED=deliver_sigint DELIVER_SIGINT=$where ../test_utils/scripts/timeout.py 30 -- \
      ansible-playbook -i inventory deliver_sigint.yml -f 10 > "${OUTPUT_DIR}/deliver_sigint.txt" 2>&1
  rc="$?"
  if [[ "$rc" != "99" ]] || ! grep -q "User interrupted execution" "${OUTPUT_DIR}/deliver_sigint.txt"; then
      echo "The SIGINT delivered in a $where did not stop the run (rc $rc)"
      cat "${OUTPUT_DIR}/deliver_sigint.txt"
      exit 1
  fi
done
