#!/usr/bin/env bash

set -ux

ansible-playbook setup.yml -i inventory -v "$@"

export ANSIBLE_KEEP_REMOTE_FILES=True
export ANSIBLE_COMMON_REMOTE_GROUP=notcoolenoughforroot
export ANSIBLE_BECOME_PASS='iWishIWereCoolEnoughForRoot!'

ansible-playbook test.yml -i inventory -v "$@"

# Do a few cleanup tasks (nuke users, groups, and homedirs, undo config changes)
ansible-playbook cleanup.yml -i inventory -v "$@"
