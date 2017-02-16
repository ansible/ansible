#!/usr/bin/env bash

set -eux

ansible-playbook play.yml -i ../../inventory -v "$@"
