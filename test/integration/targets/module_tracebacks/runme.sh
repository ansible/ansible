#!/usr/bin/env bash

set -eux

ansible-playbook traceback.yml -i inventory "$@"
