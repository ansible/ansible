#!/usr/bin/env bash

set -eux

ansible-playbook verify.yml -i generator.yml "${@}"
