#!/usr/bin/env bash

set -eux

ansible-playbook delegate_facts.yml -i inventory "$@"
