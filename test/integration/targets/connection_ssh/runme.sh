#!/usr/bin/env bash

set -ux

# We skip this whole section if the test node doesn't have sshpass on it.
if command -v sshpass > /dev/null; then
    # Check if our sshpass supports -P
    sshpass -P foo > /dev/null
    sshpass_supports_prompt=$?
    if [[ $sshpass_supports_prompt -eq 0 ]]; then
        # If the prompt is wrong, we'll end up hanging (due to sshpass hanging).
        # We should probably do something better here, like timing out in Ansible,
        # but this has been the behavior for a long time, before we supported custom
        # password prompts.
        #
        # So we search for a custom password prompt that is clearly wrong and call
        # ansible with timeout. If we time out, our custom prompt was successfully
        # searched for. It's a weird way of doing things, but it does ensure
        # that the flag gets passed to sshpass.
        ../test_utils/scripts/timeout.py 5 -- ansible -m ping \
            -e ansible_connection=ssh \
            -e ansible_ssh_password_mechanism=sshpass \
            -e ansible_sshpass_prompt=notThis: \
            -e ansible_password=foo \
            -e ansible_user=definitelynotroot \
            -i test_connection.inventory \
            ssh-pipelining
        ret=$?
        # 124 is EXIT_TIMEDOUT from gnu coreutils
        # 143 is 128+SIGTERM(15) from BusyBox
        if [[ $ret -ne 124 && $ret -ne 143 ]]; then
            echo "Expected to time out and we did not. Exiting with failure."
            exit 1
        fi
    else
        ansible -m ping \
            -e ansible_connection=ssh \
            -e ansible_ssh_password_mechanism=sshpass \
            -e ansible_sshpass_prompt=notThis: \
            -e ansible_password=foo \
            -e ansible_user=definitelynotroot \
            -i test_connection.inventory \
            ssh-pipelining | grep 'customized password prompts'
        ret=$?
        [[ $ret -eq 0 ]] || exit $ret
    fi
fi

set -e

if [[ "$(scp -O 2>&1)" == "usage: scp "* ]]; then
    # scp supports the -O option (and thus the -T option as well)
    # work-around required
    # see: https://www.openssh.com/txt/release-9.0
    scp_args=("-e" "ansible_scp_extra_args=-TO")
elif [[ "$(scp -T 2>&1)" == "usage: scp "* ]]; then
    # scp supports the -T option
    # work-around required
    # see: https://github.com/ansible/ansible/issues/52640
    scp_args=("-e" "ansible_scp_extra_args=-T")
else
    # scp does not support the -T or -O options
    # no work-around required
    # however we need to put something in the array to keep older versions of bash happy
    scp_args=("-e" "")
fi

# sftp
./posix.sh "$@"
# scp
ANSIBLE_SSH_TRANSFER_METHOD=scp ./posix.sh "$@" "${scp_args[@]}"
# piped
ANSIBLE_SSH_TRANSFER_METHOD=piped ./posix.sh "$@"

# test config defaults override
ansible-playbook check_ssh_defaults.yml "$@" -i test_connection.inventory

# ensure we can load from ini cfg
ANSIBLE_CONFIG=./test_ssh_defaults.cfg ansible-playbook verify_config.yml "$@"

# ensure we handle cp with spaces correctly, otherwise would fail with
# `"Failed to connect to the host via ssh: command-line line 0: keyword controlpath extra arguments at end of line"`
ANSIBLE_SSH_CONTROL_PATH='/tmp/ssh cp with spaces' ansible -m ping all -e ansible_connection=ssh -i test_connection.inventory "$@"

# Test that timeout on waiting on become is an unreachable error
ansible-playbook test_unreachable_become_timeout.yml "$@"

ANSIBLE_ROLES_PATH=../ ansible-playbook "$@" -i ../../inventory test_ssh_askpass.yml

# ensure that SSH client verbosity is independent of Ansible verbosity - no `debugN:` lines at high Ansible verbosity
ansible ssh -m raw -a whoami -i test_connection.inventory -vvvvv | grep -v 'debug.:'

# enable SSH client verbosity level 1 via env; ensure debugN: but no debug2 or debug3 lines
ANSIBLE_SSH_VERBOSITY=1 ansible ssh -m raw -a whoami -i test_connection.inventory -vvvvv | grep 'debug.:' | grep -v 'debug(2|3):'

# enable SSH client verbosity level 3 via var; ensure debug3 lines
ansible ssh -m raw -a whoami -i test_connection.inventory -vvvvv -e ansible_ssh_verbosity=3 2>&1 | grep 'debug3:'

echo PASS
