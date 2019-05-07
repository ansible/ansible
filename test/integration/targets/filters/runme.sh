#!/usr/bin/env bash

set -eux

source virtualenv.sh

# Requirements have to be installed prior to running ansible-playbook
# because plugins and requirements are loaded before the task runs

pip install jmespath netaddr bcrypt passlib

ANSIBLE_ROLES_PATH=../ ansible-playbook filters.yml -i ../../inventory -e @../../integration_config.yml "$@"

pip install "passlib<1.7"
ANSIBLE_ROLES_PATH=../ ansible-playbook filters.yml -t password_hash -i ../../inventory -e @../../integration_config.yml "$@"

# Required to test against CryptHash class

source virtualenv-isolated.sh

pip install jmespath netaddr bcrypt -r ../../../../requirements.txt

ANSIBLE_ROLES_PATH=../ ansible-playbook filters.yml -e crypt_run=False -t password_hash -i ../../inventory -e @../../integration_config.yml "$@"
