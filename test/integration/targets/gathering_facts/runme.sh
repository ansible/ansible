#!/usr/bin/env bash

set -eux

ansible-playbook test_gathering_facts.yml -i ../../inventory -v "$@"
