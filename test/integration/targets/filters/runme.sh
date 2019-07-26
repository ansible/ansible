#!/usr/bin/env bash

set -eux

source virtualenv.sh

# Requirements have to be installed prior to running ansible-playbook
# because plugins and requirements are loaded before the task runs

# bcrypt has to be installed w/o build isolation b/c of the Pip's bug:
# setuptools from system site-packages are leaking into an isolated
# PEP518/517 build env.
# Supposingly it's this one:
# https://github.com/pypa/pip/issues/6264#issuecomment-480100770
# Whenever that is fixed, it's okay to drop ``--no-build-isolation``
pip install --no-build-isolation bcrypt

pip install jmespath netaddr passlib

ANSIBLE_ROLES_PATH=../ ansible-playbook filters.yml "$@"
