#!/usr/bin/env bash

set -eux

export ANSIBLE_TEST_PREFER_VENV=1
source virtualenv.sh

pip install -U jinja2==2.9.4

ansible-playbook -i ../../inventory test_jinja2_groupby.yml -v "$@"

pip install -U "jinja2<2.9.0"

ansible-playbook -i ../../inventory test_jinja2_groupby.yml -v "$@"
