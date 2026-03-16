#!/usr/bin/env bash

set -eux

# We need to run these tests with both the powershell and cmd shell type

### cmd tests - no DefaultShell set ###
ansible -i ../../inventory.winrm localhost \
    -m template \
    -a "src=test_connection.inventory.j2 dest=${OUTPUT_DIR}/test_connection.inventory" \
    -e "test_shell_type=cmd" \
    "$@"

# https://github.com/PowerShell/Win32-OpenSSH/wiki/DefaultShell
ansible -i ../../inventory.winrm windows \
    -m win_regedit \
    -a "path=HKLM:\\\\SOFTWARE\\\\OpenSSH name=DefaultShell state=absent" \
    "$@"

# Need to flush the connection to ensure we get a new shell for the next tests
ansible -i "${OUTPUT_DIR}/test_connection.inventory" windows \
    -m meta -a "reset_connection" \
    "$@"

# sftp
./windows.sh "$@"
# scp
ANSIBLE_SSH_TRANSFER_METHOD=scp ./windows.sh "$@"
# other tests not part of the generic connection test framework
ansible-playbook -i "${OUTPUT_DIR}/test_connection.inventory" tests.yml \
    "$@"

### powershell tests - explicit DefaultShell set ###
# we do this last as the default shell on our CI instances is set to PowerShell
ansible -i ../../inventory.winrm localhost \
    -m template \
    -a "src=test_connection.inventory.j2 dest=${OUTPUT_DIR}/test_connection.inventory" \
    -e "test_shell_type=powershell" \
    "$@"

# ensure the default shell is set to PowerShell - use an explicit shell
# var as a previous task set the default shell to cmd and we don't want to
# inherit the ansible-test defaults in inventory.winrm.
ansible -i ../../inventory.winrm windows \
    -m win_regedit \
    -a "path=HKLM:\\\\SOFTWARE\\\\OpenSSH name=DefaultShell data=C:\\\\Windows\\\\System32\\\\WindowsPowerShell\\\\v1.0\\\\powershell.exe" \
    -e "ansible_shell_type=cmd" \
    "$@"

ansible -i "${OUTPUT_DIR}/test_connection.inventory" windows \
    -m meta -a "reset_connection" \
    "$@"

./windows.sh "$@"
ANSIBLE_SSH_TRANSFER_METHOD=scp ./windows.sh "$@"
ansible-playbook -i "${OUTPUT_DIR}/test_connection.inventory" tests.yml \
    "$@"
