#!/usr/bin/env bash

set -ux
#apk add coreutils
        timeout 5 ansible -m ping \
            -e ansible_connection=ssh \
            -e ansible_sshpass_prompt=notThis: \
            -e ansible_password=foo \
            -e ansible_user=definitelynotroot \
        -i test_connection.inventory \
            ssh-no-pipelining
        ret=$?
        # 124 is EXIT_TIMEDOUT from gnu coreutils
        # 143 is 128+SIGTERM(15) from BusyBox
        if [[ $ret -ne 124 && $ret -ne 143 ]]; then
            echo "Expected to time out and we did not. Exiting with failure."
            exit 1
        fi


echo 'made it here'

exit 1
