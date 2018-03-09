#!/usr/bin/env bash

set -ux

OUT=$(ansible-playbook playbook.yml -i inventory -e @../../integration_config.yml "$@" 2>&1 | grep 'ERROR! Module "tags" shadows the name of a reserved keyword.')

if [[ -z "$OUT" ]]; then
    echo "Fake tags module did not cause error"
    exit 1
fi

# This playbook calls a lookup which shadows a keyword.
# This is an ok situation, and should not error
ansible-playbook playbook_lookup.yml -i inventory -e @../../integration_config.yml "$@"
