#!/usr/bin/env bash

set -eux

ansible-playbook -i ../../inventory play.yml "$@"

ansible-playbook validate_broken_conditionals.yml "$@"
