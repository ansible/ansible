#!/usr/bin/env bash

set -eux

ansible-playbook test_templating_settings.yml -i ../../inventory -v "$@"
