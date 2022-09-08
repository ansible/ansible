#!/usr/bin/env bash

set -euxv

# 'real script'
ansible-playbook realpath.yml "$@" --vault-password-file script/vault-secret.sh

# using symlink
ansible-playbook symlink.yml "$@" --vault-password-file symlink/get-password-symlink

### NEGATIVE TESTS

ER='Attempting to decrypt'
#### no secrets
# 'real script'
ansible-playbook realpath.yml "$@" 2>&1 |grep "${ER}"

# using symlink
ansible-playbook symlink.yml "$@" 2>&1 |grep "${ER}"

ER='Decryption failed'
### wrong secrets
# 'real script'
ansible-playbook realpath.yml "$@" --vault-password-file symlink/get-password-symlink 2>&1 |grep "${ER}"

# using symlink
ansible-playbook symlink.yml "$@" --vault-password-file script/vault-secret.sh 2>&1 |grep "${ER}"
