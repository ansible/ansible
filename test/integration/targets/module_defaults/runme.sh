#!/usr/bin/env bash

set -ux

ansible-playbook -i inventory -e @../../integration_config.yml "$@" tasks/main.yml | tee out.txt
res=$?
cat out.txt
if [ "${res}" -ne 0 ] ; then
    exit 1
fi

ansible-playbook -i inventory -e @../../integration_config.yml "$@" tasks/merge_module_defaults_false.yml | tee out.txt
res=$?
cat out.txt
if [ "${res}" -ne 0 ] ; then
    exit 1
fi

export ANSIBLE_MODULE_DEFAULTS_MERGE=True

ansible-playbook -i inventory -e @../../integration_config.yml "$@" tasks/merge_module_defaults_true.yml | tee out.txt
res=$?
cat out.txt

exit $res
