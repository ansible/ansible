#!/usr/bin/env bash

set -eux

# This test expects 7 loggable vars and 0 non-loggable ones.
# If either mismatches it fails, run the ansible-playbook command to debug.

[ "$(ansible-playbook no_log_local.yml -i ../../inventory -vvvvv "$@" | awk \
'BEGIN { logme = 0; nolog = 0; } /LOG_ME/ { logme += 1;} /DO_NOT_LOG/ { nolog += 1;} END { printf "%d/%d", logme, nolog; }')" = "26/0" ]
