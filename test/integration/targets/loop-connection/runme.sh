#!/usr/bin/env bash

set -eux -o pipefail

ansible-playbook main.yml "$@"
