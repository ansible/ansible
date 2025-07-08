#!/usr/bin/env bash

set -eux -o pipefail

# ensure _ansible_no_log returned by actions is actually respected
ansible-playbook ansible_no_log_in_result.yml -vvvvv > "${OUTPUT_DIR}/output.log" 2> /dev/null

[ "$(grep -c "action result should be masked" "${OUTPUT_DIR}/output.log")" = "0" ]
[ "$(grep -c "the output has been hidden" "${OUTPUT_DIR}/output.log")" = "4" ]

# This test expects 7 loggable vars and 0 non-loggable ones.
# If either mismatches it fails, run the ansible-playbook command to debug.
[ "$(ansible-playbook no_log_local.yml -i ../../inventory -vvvvv "$@" | awk \
'BEGIN { logme = 0; nolog = 0; } /LOG_ME/ { logme += 1;} /DO_NOT_LOG/ { nolog += 1;} END { printf "%d/%d", logme, nolog; }')" = "26/0" ]

# deal with corner cases with no log and loops
# no log enabled, should produce 6 censored messages
[ "$(ansible-playbook dynamic.yml -i ../../inventory -vvvvv "$@" -e unsafe_show_logs=no|grep -c 'output has been hidden')" = "7" ]

# no log disabled, should produce 0 censored
[ "$(ansible-playbook dynamic.yml -i ../../inventory -vvvvv "$@" -e unsafe_show_logs=yes|grep -c 'output has been hidden')" = "0" ]

# test no log for sub options
[ "$(ansible-playbook no_log_suboptions.yml -i ../../inventory -vvvvv "$@" | grep -Ec 'SECRET')" = "0" ]

# test invalid data passed to a suboption
[ "$(ansible-playbook no_log_suboptions_invalid.yml -i ../../inventory -vvvvv "$@" | grep -Ec 'SECRET')" = "0" ]

# test variations on ANSIBLE_NO_LOG
[ "$(ansible-playbook no_log_config.yml -i ../../inventory -vvvvv "$@" | grep -Ec 'the output has been hidden')" = "1" ]
[ "$(ANSIBLE_NO_LOG=0 ansible-playbook no_log_config.yml -i ../../inventory -vvvvv "$@" | grep -Ec 'the output has been hidden')" = "1" ]
[ "$(ANSIBLE_NO_LOG=1 ansible-playbook no_log_config.yml -i ../../inventory -vvvvv "$@" | grep -Ec 'the output has been hidden')" = "5" ]
