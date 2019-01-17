#!/usr/bin/env bash

set -eux

ansible-playbook test_templating_settings.yml -i ../../inventory -v "$@"
ansible-playbook warn_on_register.yml -i ../../inventory -v "$@"| grep 'is not templatable, but we found'
