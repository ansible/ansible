#!/usr/bin/env bash

set -ux

ansible-playbook -i this,path,has,commas/hosts playbook.yml -v "$@"
