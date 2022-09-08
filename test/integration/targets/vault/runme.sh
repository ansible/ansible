#!/usr/bin/env bash

set -eux

# 'real script'
ansible-playbook realpath.yml "$@" --vault-password-file script/vault-secret.sh

# using symlink
ansible-playbook symlink.yml "$@" --vault-password-file symlink/get-password-symlink

### NEGATIVE TESTS

#### no secrets
# 'real script'
ansible-playbook realpath.yml "$@" || /bin/true

# using symlink
ansible-playbook symlink.yml "$@" || /bin/true

### wrong secrets
# 'real script'
ansible-playbook realpath.yml "$@" --vault-password-file symlink/get-password-symlink || /bin/true

# using symlink
ansible-playbook symlink.yml "$@" --vault-password-file script/vault-secret.sh || /bin/true
