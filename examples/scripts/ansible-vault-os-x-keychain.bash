#!/usr/bin/env bash
#
# This bash wrapper allows me to use ansible-vault in combination with OS X's
# Keychain for securely handling the encryption password with no input. No
# prompts, to typos, same security as SSH key passphrases.
#
# I am using the "Ansible Vault" application password entry for the
# "ansible_vault" accountt which I have manually added to Keychain. I have this
# wrapper saved as $HOME/bin/av:
#
#   av edit group_vars/encrypted_vars.yml
#
# The above command will fetch the ansible_vault password from the Keychain,
# store it in a temporary file, use it to decrypt the file and allow me to edit
# it, then safely removes the temporary copy of the password.
#
# This bash script could be extended to make the password host-specific, but
# for my purposes it's enough in its current form.

tmpfile=$(mktemp -t vault)

ensure_tmpfile_gets_removed() {
  rm -f $tmpfile
}

trap ensure_tmpfile_gets_removed EXIT

echo $(security find-generic-password -a ansible_vault -w) > $tmpfile

command="$1"
shift
args=$@

ansible-vault $command $args --vault-password-file $tmpfile
