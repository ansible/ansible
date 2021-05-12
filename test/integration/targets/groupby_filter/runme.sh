#!/usr/bin/env bash

set -eux

export ANSIBLE_TEST_PREFER_VENV=1
source virtualenv.sh

# Update pip in the venv to a version that supports constraints
pip install --requirement requirements.txt

pip install -U jinja2==2.9.4 --constraint "../../../lib/ansible_test/_data/requirements/constraints.txt"

ansible-playbook -i ../../inventory test_jinja2_groupby.yml -v "$@"

pip install -U "jinja2<2.9.0" --constraint "../../../lib/ansible_test/_data/requirements/constraints.txt"

ansible-playbook -i ../../inventory test_jinja2_groupby.yml -v "$@"
