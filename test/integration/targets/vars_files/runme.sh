#!/usr/bin/env bash

set -eux

ansible-playbook runme.yml -i inventory -v "$@"

set +e
# These should fail, if they succeed, that is bad, so we basicall swap the RCs
ansible-playbook unresolvable.yml -i inventory -v "$@"
unresolvable_rc=$?
if [ "$unresolvable_rc" == "0" ]; then
    echo "unresolvable.yml should have expectedly failed, not succeeded"
    exit 1
fi

ansible-playbook unresolvable2.yml -i inventory -v "$@"
unresolvable2_rc=$?
if [ "$unresolvable2_rc" == "0" ]; then
    echo "unresolvable2.yml should have expectedly failed, not succeeded"
    exit 1
fi

set -e
