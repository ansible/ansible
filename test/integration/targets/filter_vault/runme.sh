#!/usr/bin/env bash

set -eux

ansible-playbook base.yml "$@"
