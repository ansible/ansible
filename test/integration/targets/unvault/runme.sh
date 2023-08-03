#!/usr/bin/env bash

set -eux

# simple run
ansible-playbook --vault-password-file password main.yml

# runs only with id
ansible-playbook --vault-id test1@id_password main.yml --tags use_id
