#!/usr/bin/env bash

set -eux

export ANSIBLE_ROLES_PATH=./roles

python runme.py -i ../../inventory "$@"

# # Test with no args
# spawn ansible -i ../../inventory testhost -m pause
# expect "Press enter to continue, Ctrl+C to abort:"
# send "\r"

# # Test with pause and abort
# spawn ansible -i ../../inventory testhost -m pause -a seconds=5
# expect "(ctrl+C then 'C' = continue early, ctrl+C then 'A' = abort)"
# send "^Ca"

# # Test with pause and continue
# spawn ansible-playbook -i ../../inventory test-pause.yml
# expect "(ctrl+C then 'C' = continue early, ctrl+C then 'A' = abort)"
# send "^Cc"



