#!/usr/bin/env bash

set -eux

ANSIBLE_CONDITIONAL_BARE_VARS=1 ansible-playbook -i ../../inventory play.yml "$@"
ANSIBLE_CONDITIONAL_BARE_VARS=0 ansible-playbook -i ../../inventory play.yml "$@"
