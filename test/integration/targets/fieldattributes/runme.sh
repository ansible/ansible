#!/usr/bin/env bash

set -eux

ansible-playbook private.yml "$@" && exit 1 || exit 0
