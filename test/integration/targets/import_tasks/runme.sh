#!/usr/bin/env bash

set -eux

ansible-playbook inherit_notify.yml "$@"
