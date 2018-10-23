#!/usr/bin/env bash

set -ux

# Modules that shadow keywords are ignored, this should succeed without issue
ansible-playbook playbook.yml -i inventory -e @../../integration_config.yml "$@"

# This playbook calls a lookup which shadows a keyword.
# This is an ok situation, and should not error
ansible-playbook playbook_lookup.yml -i ../../inventory -e @../../integration_config.yml "$@"
