#!/usr/bin/env bash

set -eux -o pipefail

ansible --version
ansible --help

ansible testhost -i ../../inventory -m ping  "$@"
ansible testhost -i ../../inventory -m setup "$@"

ansible-config view -c ./ansible-testé.cfg | grep 'remote_user = admin'
ansible-config dump -c ./ansible-testé.cfg | grep 'DEFAULT_REMOTE_USER([^)]*) = admin\>'
ANSIBLE_REMOTE_USER=administrator ansible-config dump| grep 'DEFAULT_REMOTE_USER([^)]*) = administrator\>'
ansible-config list | grep 'DEFAULT_REMOTE_USER'

# 'view' command must fail when config file is missing
ansible-config view -c ./ansible-non-existent.cfg && exit 1 || echo 'Failure is expected'
