#!/usr/bin/env bash

set -eux

trap 'rm -f out' EXIT

ansible-playbook main.yml -i ../../inventory | tee out
for i in 1 2 3; do
  grep "ok: \[localhost\] => (item=$i)" out
  grep "\"item\": $i" out
done

ansible-playbook main_fqcn.yml -i ../../inventory | tee out
for i in 1 2 3; do
  grep "ok: \[localhost\] => (item=$i)" out
  grep "\"item\": $i" out
done

# ensure debug does not set top level vars when looking at ansible_facts
ansible-playbook nosetfacts.yml "$@"
