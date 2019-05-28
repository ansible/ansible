#!/usr/bin/env bash

set -eux

# Verify that extra data before module JSON output during async call is ignored.
ANSIBLE_DEBUG=0 LC_ALL=bogus ansible-playbook test_async.yml -i inventory -v "$@"
# Verify that the warning exists by examining debug output.
ANSIBLE_DEBUG=1 LC_ALL=bogus ansible-playbook test_async.yml -i inventory -v "$@" \
    | grep 'bash: warning: setlocale: LC_ALL: cannot change locale (bogus)' > /dev/null
