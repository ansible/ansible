#!/usr/bin/env bash

set -ux
ansible-playbook -i inventory "$@" play_level.yml| tee out.txt | grep 'any_errors_fatal_play_level_post_fail'
res=$?
cat out.txt
if [ "${res}" -eq 0 ] ; then
    exit 1
fi

ansible-playbook -i inventory "$@" on_includes.yml | tee out.txt | grep 'any_errors_fatal_this_should_never_be_reached'
res=$?
cat out.txt
if [ "${res}" -eq 0 ] ; then
    exit 1
fi

ansible-playbook -i inventory "$@" always_block.yml | tee out.txt | grep 'any_errors_fatal_always_block_start'
res=$?
cat out.txt

if [ "${res}" -ne 0 ] ; then
    exit 1
fi

for test_name in test_include_role test_include_tasks; do
  ansible-playbook -i inventory "$@" -e test_name=$test_name 50897.yml | tee out.txt | grep 'any_errors_fatal_this_should_never_be_reached'
  res=$?
  cat out.txt
  if [ "${res}" -eq 0 ] ; then
      exit 1
  fi
done

set -e

ansible-playbook -i inventory "$@" 31543.yml | tee out.txt
[ "$(grep -c 'SHOULD NOT HAPPEN' out.txt)" -eq 0 ]

ansible-playbook -i inventory "$@" 36308.yml | tee out.txt
[ "$(grep -c 'handler1 ran' out.txt)" -eq 1 ]

ansible-playbook -i inventory "$@" 73246.yml | tee out.txt
[ "$(grep -c 'PASSED' out.txt)" -eq 1 ]

ansible-playbook -i inventory "$@" 80981.yml | tee out.txt
[ "$(grep -c 'SHOULD NOT HAPPEN' out.txt)" -eq 0 ]
[ "$(grep -c 'rescuedd' out.txt)" -eq 2 ]
[ "$(grep -c 'recovered' out.txt)" -eq 2 ]
