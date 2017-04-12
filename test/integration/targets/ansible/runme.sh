#!/usr/bin/env bash

set -eux

env

which python
python --version

which ansible
ansible --version
ansible testhost -i ../../inventory -vvv -e "ansible_python_interpreter=$(which python)" -m ping
ansible testhost -i ../../inventory -vvv -e "ansible_python_interpreter=$(which python)" -m setup
