#!/usr/bin/env bash

set -eux

# ignore empty env var and use default
# shellcheck disable=SC1007
ANSIBLE_TIMEOUT= ansible -m ping testhost -i ../../inventory "$@"

# env var is wrong type, this should be a fatal error pointing at the setting
ANSIBLE_TIMEOUT='lola' ansible -m ping testhost -i ../../inventory "$@" 2>&1|grep 'Invalid type for configuration option setting: DEFAULT_TIMEOUT'

# https://github.com/ansible/ansible/issues/69577
ANSIBLE_REMOTE_TMP="$HOME/.ansible/directory_with_no_space"  ansible -m ping testhost -i ../../inventory "$@"

ANSIBLE_REMOTE_TMP="$HOME/.ansible/directory with space"  ansible -m ping testhost -i ../../inventory "$@"

ANSIBLE_CONFIG=nonexistent.cfg ansible-config dump --only-changed -v | grep 'No config file found; using defaults'

# https://github.com/ansible/ansible/pull/73715
ANSIBLE_CONFIG=inline_comment_ansible.cfg ansible-config dump --only-changed | grep "'ansibull'"

# test the config option validation
ansible-playbook validation.yml "$@"

# test types from config (just lists for now)
ANSIBLE_CONFIG=type_munging.cfg ansible-playbook types.yml "$@"

cleanup() {
	rm -f files/*.new.*
}

trap 'cleanup' EXIT

diff_failure() {
    if [[ $INIT = 0 ]]; then
        echo "FAILURE...diff mismatch!"
        exit 1
    fi
}
# check a-c init per format
ANSIBLE_LOOKUP_PLUGINS=./ ansible-config init types -t lookup -f ini > files/types.new.ini
diff -u files/types.ini files/types.new.ini || diff_failure

ANSIBLE_LOOKUP_PLUGINS=./ ansible-config init types -t lookup -f vars > files/types.new.yml
diff -u files/types.yml files/types.new.yml || diff_failure

ANSIBLE_LOOKUP_PLUGINS=./ ansible-config init types -t lookup -f env > files/types.new.env
diff -u files/types.env files/types.new.env || diff_failure


