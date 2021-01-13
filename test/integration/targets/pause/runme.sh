#!/usr/bin/env bash

set -eux

ANSIBLE_ROLES_PATH=../ ansible-playbook setup.yml

# Test pause module when no tty and non-interactive with no seconds parameter.
# This is to prevent playbooks from hanging in cron and Tower jobs.
/usr/bin/env bash << EOF
ansible-playbook test-pause-no-tty.yml 2>&1 | \
    grep '\[WARNING\]: Not waiting for response to prompt as stdin is not interactive' && {
        echo 'Successfully skipped pause in no TTY mode' >&2
        exit 0
    } || {
        echo 'Failed to skip pause module' >&2
        exit 1
    }
EOF

# Do not issue a warning when run in the background if a timeout is given
# https://github.com/ansible/ansible/issues/73042
if sleep 0 | ansible localhost -m pause -a 'seconds=1' 2>&1 | grep '\[WARNING\]: Not waiting for response'; then
    echo "Incorrectly issued warning when run in the background"
    exit 1
else
    echo "Succesfully ran in the background with no warning"
fi

# Test redirecting stdout
# https://github.com/ansible/ansible/issues/41717
if ansible-playbook pause-3.yml > /dev/null ; then
    echo "Successfully redirected stdout"
else
    echo "Failure when attempting to redirect stdout"
    exit 1
fi


# Test pause with seconds and minutes specified
ansible-playbook test-pause.yml "$@"

# Interactively test pause
python test-pause.py "$@"
