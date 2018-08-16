#!/usr/bin/env bash

set -ux


# check normal execution
for myplay in normal/*.yml
do
	ansible-playbook "${myplay}" -i ../../inventory -vvv "$@"
	if test $? != 0 ; then
		echo "### Failed to run ${myplay} normally"
		exit 1
	fi
done

# check overrides
for myplay in override/*.yml
do
	ansible-playbook "${myplay}" -i ../../inventory -vvv "$@"
	if test $? != 0 ; then
		echo "### Failed to run ${myplay} override"
		exit 1
	fi
done
