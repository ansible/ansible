#!/usr/bin/env bash

set -ux
ansible-playbook -i ../../inventory -e @../../integration_config.yml "$@" play_level.yml| tee out.txt | grep 'any_errors_fatal_play_level_post_fail'

res=$?
if [ "${res}" -eq 0 ] ; then
	exit 1
fi

ansible-playbook -i ../../inventory -e @../../integration_config.yml "$@" on_includes.yml | tee out.txt | grep 'any_errors_fatal_this_should_never_be_reached'
res=$?
if [ "${res}" -eq 0 ] ; then
	exit 1
fi

set -eux

ansible-playbook -i ../../inventory -e @../../integration_config.yml "$@" always_block.yml | tee out.txt | grep 'any_errors_fatal_always_block_start'

exit $?
