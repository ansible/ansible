#!/usr/bin/env bash

set -eux

ansible-playbook -i ../../inventory play.yml "$@"
