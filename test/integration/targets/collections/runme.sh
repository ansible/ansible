#!/usr/bin/env bash

set -eux

export ANSIBLE_INSTALLED_CONTENT_ROOTS=$PWD/collection_root_user,$PWD/collection_root_sys
export ANSIBLE_GATHERING=explicit
export ANSIBLE_GATHER_SUBSET=minimal

ansible-playbook -i ../../inventory -i ./a.statichost.yml -v play.yml

