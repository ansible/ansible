#!/usr/bin/env bash

set -eux

ANSIBLE_INVENTORY_ENABLED=notyaml ansible-playbook subdir/play.yml -i notyaml.yml "$@"
