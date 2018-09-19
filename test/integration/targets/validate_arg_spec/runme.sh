#!/usr/bin/env bash

set -euvx

# if you need to point to a custom ansible-playbook, perhaps
# one with logging enabled
ANSIBLE_PLAYBOOK=${ANSIBLE_PLAYBOOK:-"ansible-playbook"}

# test with some bogus argspecs that shoudl cause validate_arg_spec to fail
"$ANSIBLE_PLAYBOOK" -i ../../inventory -v "$@" test_include_role_fails.yml

# test with valid arg specs
"$ANSIBLE_PLAYBOOK" -i ../../inventory -v "$@" test_include_role.yml

# not sure what is going on here, multiple import_role tasks seem to clobber each others vars:
# "$ANSIBLE_PLAYBOOK" -i ../../inventory -v "$@" -e @../../integration_config.yml test_import_role.yml
"$ANSIBLE_PLAYBOOK" -i ../../inventory -v "$@" -e @../../integration_config.yml test_play_level_role.yml

# test calling validate_arge_spec as a task directly
"$ANSIBLE_PLAYBOOK" -i ../../inventory -v "$@" -e @../../integration_config.yml test_validate_arg_spec_task.yml
