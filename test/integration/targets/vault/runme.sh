#!/usr/bin/env bash

set -eux

MYTMPDIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')
trap 'rm -rf "${MYTMPDIR}"' EXIT

# create a test file
TEST_FILE="${MYTMPDIR}/test_file"
echo "This is a test file" > "${TEST_FILE}"

TEST_FILE_OUTPUT="${MYTMPDIR}/test_file_output"

# old format
ansible-vault view "$@" --vault-password-file vault-password-ansible format_1_0_AES.yml

ansible-vault view "$@" --vault-password-file vault-password-ansible format_1_1_AES.yml

# old format, wrong password
echo "The wrong password tests are expected to return 1"
ansible-vault view "$@" --vault-password-file vault-password-wrong format_1_0_AES.yml && :
WRONG_RC=$?
echo "rc was $WRONG_RC (1 is expected)"
[ $WRONG_RC -eq 1 ]

ansible-vault view "$@" --vault-password-file vault-password-wrong format_1_1_AES.yml && :
WRONG_RC=$?
echo "rc was $WRONG_RC (1 is expected)"
[ $WRONG_RC -eq 1 ]

ansible-vault view "$@" --vault-password-file vault-password-wrong format_1_1_AES256.yml && :
WRONG_RC=$?
echo "rc was $WRONG_RC (1 is expected)"
[ $WRONG_RC -eq 1 ]

set -eux

# new format, view
ansible-vault view "$@" --vault-password-file vault-password format_1_1_AES256.yml

# encrypt it
ansible-vault encrypt "$@" --vault-password-file vault-password "${TEST_FILE}"

ansible-vault view "$@" --vault-password-file vault-password "${TEST_FILE}"

ansible-vault decrypt "$@" --vault-password-file vault-password "${TEST_FILE}"

# new password file for rekeyed file
NEW_VAULT_PASSWORD="${MYTMPDIR}/new-vault-password"
echo "newpassword" > "${NEW_VAULT_PASSWORD}"

ansible-vault encrypt "$@" --vault-password-file vault-password "${TEST_FILE}"

ansible-vault rekey "$@" --vault-password-file vault-password --new-vault-password-file "${NEW_VAULT_PASSWORD}" "${TEST_FILE}"

ansible-vault view "$@" --vault-password-file "${NEW_VAULT_PASSWORD}" "${TEST_FILE}"

ansible-vault decrypt "$@" --vault-password-file "${NEW_VAULT_PASSWORD}" "${TEST_FILE}"

# reading/writing to/from stdin/stdin  (See https://github.com/ansible/ansible/issues/23567)
ansible-vault encrypt "$@" --vault-password-file "${NEW_VAULT_PASSWORD}" --output="${TEST_FILE_OUTPUT}" < "${TEST_FILE}"
ansible-vault view "$@" --vault-password-file "${NEW_VAULT_PASSWORD}" - < "${TEST_FILE_OUTPUT}"
ansible-vault decrypt "$@" --vault-password-file "${NEW_VAULT_PASSWORD}" --output=- < "${TEST_FILE_OUTPUT}"

ansible-vault encrypt_string "$@" --vault-password-file "${NEW_VAULT_PASSWORD}" "a test string"

ansible-vault encrypt_string "$@" --vault-password-file "${NEW_VAULT_PASSWORD}" --name "blippy" "a test string names blippy"


# from stdin
ansible-vault encrypt_string "$@" --vault-password-file "${NEW_VAULT_PASSWORD}" < "${TEST_FILE}"

ansible-vault encrypt_string "$@" --vault-password-file "${NEW_VAULT_PASSWORD}" --stdin-name "the_var_from_stdin" < "${TEST_FILE}"

# write to file
ansible-vault encrypt_string "$@" --vault-password-file "${NEW_VAULT_PASSWORD}" --name "blippy" "a test string names blippy" --output "${MYTMPDIR}/enc_string_test_file"


# test playbooks using vaulted files
ansible-playbook test_vault.yml          -i ../../inventory -v "$@" --vault-password-file vault-password --list-tasks
ansible-playbook test_vault.yml          -i ../../inventory -v "$@" --vault-password-file vault-password --list-hosts
ansible-playbook test_vault.yml          -i ../../inventory -v "$@" --vault-password-file vault-password --syntax-check
ansible-playbook test_vault.yml          -i ../../inventory -v "$@" --vault-password-file vault-password
ansible-playbook test_vault_embedded.yml -i ../../inventory -v "$@" --vault-password-file vault-password --syntax-check
ansible-playbook test_vault_embedded.yml -i ../../inventory -v "$@" --vault-password-file vault-password
ansible-playbook test_vaulted_inventory.yml -i vaulted.inventory -v "$@" --vault-password-file vault-password
ansible-playbook test_vaulted_template.yml -i ../../inventory -v "$@" --vault-password-file vault-password
