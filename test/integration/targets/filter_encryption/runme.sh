#!/usr/bin/env bash

set -eux

ANSIBLE_GATHER_SUBSET='min' ansible-playbook base.yml "$@"
