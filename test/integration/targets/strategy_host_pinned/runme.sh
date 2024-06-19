#!/usr/bin/env bash

export ANSIBLE_STDOUT_CALLBACK=callback_host_count

# the number of forks matter, see callback_plugins/callback_host_count.py
ansible-playbook --inventory hosts --forks 2 playbook.yml
