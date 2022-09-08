#!/usr/bin/env bash

set -eux

# 'real script'
ansible-playbook realpath.yml -i inventory "$@" --vault-password-file script/vault-secret.sh

# using symlink
ansible-playbook symlink.yml -i inventory "$@" --vault-password-file symlink/get-password-symlink

### NEGATIVE TESTS

#### no secrets
# 'real script'
ansible-playbook realpath.yml -i inventory "$@" || /bin/true

# using symlink
ansible-playbook symlink.yml -i inventory "$@" || /bin/true

### wrong secrets
# 'real script'
ansible-playbook realpath.yml -i inventory "$@" --vault-password-file symlink/get-password-symlink || /bin/true

# using symlink
ansible-playbook symlink.yml -i inventory "$@" --vault-password-file script/vault-secret.sh || /bin/true
