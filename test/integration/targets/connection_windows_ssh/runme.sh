#!/usr/bin/env bash

set -eux

# template out the inventory file that's based on the current Windows host details
ansible -i ../../inventory.winrm localhost \
    -m template \
    -a "src=test_connection.inventory.j2 dest=~/ansible_testing/test_connection.inventory" \
    "$@"

# ensure the default shell is set to PowerShell
# https://github.com/PowerShell/Win32-OpenSSH/wiki/DefaultShell
ansible -i ../../inventory.winrm windows \
    -m win_regedit \
    -a "path=HKLM:\\\\SOFTWARE\\\\OpenSSH name=DefaultShell data=C:\\\\Windows\\\\System32\\\\WindowsPowerShell\\\\v1.0\\\\powershell.exe" \
    "$@"

# sftp
./windows.sh "$@"
# scp
ANSIBLE_SCP_IF_SSH=true ./windows.sh "$@"

ansible-playbook -i ~/ansible_testing/test_connection.inventory tests.yml \
    "$@"
