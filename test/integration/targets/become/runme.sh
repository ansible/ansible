#!/usr/bin/env bash

set -eux

# do prev tests as role
ANSIBLE_ROLES_PATH=./ ansible -i ../inventory -m import_role -a 'name=become' "$@"

# avoid injection via user setting
ansible-playbook bad_become_user.yml -i ../inventory "$@"
