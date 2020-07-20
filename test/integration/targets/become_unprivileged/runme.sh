#!/usr/bin/env bash

set -eux

begin_sandwich() {
    ansible-playbook setup_unpriv_users.yml -i inventory -v "$@"
}

end_sandwich() {
    unset ANSIBLE_KEEP_REMOTE_FILES
    unset ANSIBLE_COMMON_REMOTE_GROUP
    unset ANSIBLE_BECOME_PASS

    # Do a few cleanup tasks (nuke users, groups, and homedirs, undo config changes)
    ansible-playbook cleanup_unpriv_users.yml -i inventory -v "$@"

    # We do these last since they do things like remove groups and will error
    # if there are still users in them.
    for pb in */cleanup.yml; do
        ansible-playbook "$pb" -i inventory -v "$@"
    done
}

trap "end_sandwich \"\$@\"" EXIT

# Common group tests
begin_sandwich "$@"
  ansible-playbook common_remote_group/setup.yml -i inventory -v "$@"
  export ANSIBLE_KEEP_REMOTE_FILES=True
  export ANSIBLE_COMMON_REMOTE_GROUP=commongroup
  export ANSIBLE_BECOME_PASS='iWishIWereCoolEnoughForRoot!'
  ANSIBLE_ACTION_PLUGINS="$(pwd)/action_plugins"
  export ANSIBLE_ACTION_PLUGINS
  ansible-playbook common_remote_group/test.yml -i inventory -v "$@"
end_sandwich "$@"
