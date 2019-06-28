#!/usr/bin/env bash

set -eux -o pipefail

ansible --version
ansible --help

ansible testhost -i ../../inventory -m ping  "$@"
ansible testhost -i ../../inventory -m setup "$@"

ansible-config -c ./ansible-testé.cfg view | grep 'remote_user = admin'
ansible-config -c ./ansible-testé.cfg dump | grep 'DEFAULT_REMOTE_USER([^)]*) = admin\>'
ANSIBLE_REMOTE_USER=administrator ansible-config dump| grep 'DEFAULT_REMOTE_USER([^)]*) = administrator\>'
ansible-config list | grep 'DEFAULT_REMOTE_USER'

# 'view' command must fail when config file is missing or has an invalid file extension
ansible-config view -c ./ansible-non-existent.cfg 2> err1.txt || grep -Eq '(FileNotFoundError|IOError): \[Errno [0-9]+\] No such file or directory' err1.txt || (cat err*.txt; rm -f err1.txt; exit 1)
ansible-config view -c ./no-extension 2> err2.txt || grep -q 'Unsupported configuration file extension' err2.txt || (cat err2.txt; rm -f err*.txt; exit 1)
rm -f err*.txt

# Test that no tmp dirs are left behind when running ansible-config
TMP_DIR=~/.ansible/tmptest
if [[ -d "$TMP_DIR" ]]; then
    rm -rf "$TMP_DIR"
fi
ANSIBLE_LOCAL_TEMP="$TMP_DIR" ansible-config list > /dev/null
ANSIBLE_LOCAL_TEMP="$TMP_DIR" ansible-config dump > /dev/null
ANSIBLE_LOCAL_TEMP="$TMP_DIR" ansible-config view > /dev/null

# wc on macOS is dumb and returns leading spaces
file_count=$(find "$TMP_DIR" -type d -maxdepth 1  | wc -l | sed 's/^ *//')
if [[ $file_count -ne 1 ]]; then
    echo "$file_count temporary files were left behind by ansible-config"
    if [[ -d "$TMP_DIR" ]]; then
        rm -rf "$TMP_DIR"
    fi
    exit 1
fi
