#!/usr/bin/env bash

set -eux

ansible-playbook module_output_cleaning.yml "$@"
