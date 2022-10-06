#!/usr/bin/env bash

set -eux

# positive inheritance works
ANSIBLE_ROLES_PATH=../ ansible-playbook 48673.yml 75692.yml  -i ../../inventory -v "$@"

# ensure negative also works
ansible-playbook -C C75692.yml -i ../../inventory -v "$@"	# expects 'foo' not to exist
ansible-playbook C75692.yml -i ../../inventory -v "$@"		# creates 'foo'
ansible-playbook -C C75692.yml -i ../../inventory -v "$@"	# expects 'foo' does exist
