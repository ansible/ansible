#!/usr/bin/env bash

set -eux

ansible-playbook test_includes.yml -i ../../inventory "$@"

ansible-playbook inherit_notify.yml "$@"
