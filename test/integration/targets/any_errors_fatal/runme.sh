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

ansible-playbook -i inventory "$@" 61025-dynamic_block.yml | tee out.txt | grep 'any_errors_fatal_dynamic_value_continues'
res=$?
cat out.txt
if [ "${res}" -ne 0 ] ; then
	exit 1
fi

ansible-playbook -i inventory "$@" 61025-import_playbook.yml | tee out.txt | grep 'any_errors_fatal_dynamic_value_import_playbook_continues'
res=$?
cat out.txt
if [ "${res}" -ne 0 ] ; then
	exit 1
fi

ansible-playbook -i inventory "$@" 61025-bad_dynamic_value.yml 2>&1 | tee out.txt | grep 'not a valid boolean.'
res=$?
cat out.txt
if [ "${res}" -ne 0 ] ; then
	exit 1
fi
