#!/usr/bin/env bash

set -eux

export ANSIBLE_KEEP_REMOTE_FILES=True
ANSIBLE_ACTION_PLUGINS="$(pwd)/action_plugins"
export ANSIBLE_ACTION_PLUGINS
export ANSIBLE_BECOME_PASS='iWishIWereCoolEnoughForRoot!'

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
# Skip on macOS, chmod fallback will take over.
# 1) chmod is stupidly hard to disable, so hitting this test case on macOS would
#    be a suuuuuuper edge case scenario
# 2) even if we can trick it so chmod doesn't exist, then other things break.
#    Ansible wants a `chmod` around, even if it's not the final thing that gets
#    us enough permission to run the task.
if [[ "$OSTYPE" != darwin* ]]; then
  begin_sandwich "$@"
    ansible-playbook common_remote_group/setup.yml -i inventory -v "$@"
    export ANSIBLE_COMMON_REMOTE_GROUP=commongroup
    ansible-playbook common_remote_group/test.yml -i inventory -v "$@"
  end_sandwich "$@"
fi

if [[ "$OSTYPE" == darwin* ]]; then
  begin_sandwich "$@"
    # In the default case this should happen on macOS, so no need for a setup
    # It should just work.
    ansible-playbook chmod_acl_macos/test.yml -i inventory -v "$@"
  end_sandwich "$@"
fi
