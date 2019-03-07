#!/usr/bin/env bash

set -euxo pipefail

ANSIBLE_VAULT_PASS_FILE=vault_pass
SSH_PRIVATE_KEY_FILE=rsa_key

VAULT_PASS_ARG=--vault-password-file=../connection_ssh/"${ANSIBLE_VAULT_PASS_FILE}"
export ANSIBLE_PRIVATE_KEY_FILE=../connection_ssh/"${SSH_PRIVATE_KEY_FILE}"

# generate a random alpha-numeric 64 characters long password
dd count=1 if=/dev/urandom | LC_CTYPE=C tr -cd "[:alpha:][:digit:]" | head -c 64 > "${ANSIBLE_VAULT_PASS_FILE}"

# generate an SSH key with an empty password
ssh-keygen -N "" -f "${SSH_PRIVATE_KEY_FILE}"

# encrypt it
ansible-vault encrypt "${VAULT_PASS_ARG}" "${SSH_PRIVATE_KEY_FILE}"

# sftp
./posix.sh "${VAULT_PASS_ARG}" "$@"
# scp
ANSIBLE_SCP_IF_SSH=true ./posix.sh "${VAULT_PASS_ARG}" "$@"
# piped
ANSIBLE_SSH_TRANSFER_METHOD=piped ./posix.sh "${VAULT_PASS_ARG}" "$@"

# cleanup
rm -fv "${SSH_PRIVATE_KEY_FILE}" "${ANSIBLE_VAULT_PASS_FILE}"
