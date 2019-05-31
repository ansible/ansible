#!/usr/bin/env bash

set -eux

ansible-playbook unsafe.yml "$@"|grep 'item.comment'|grep 'ansible_playbook_python'
