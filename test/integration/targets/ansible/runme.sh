#!/usr/bin/env bash

set -eux -o pipefail

ansible --version
ansible --help

ansible testhost -i ../../inventory -m ping  "$@"
ansible testhost -i ../../inventory -m setup "$@"

ansible-config view -c ./ansible-testé.cfg | grep 'remote_user = admin'
ansible-config dump -c ./ansible-testé.cfg | grep 'DEFAULT_REMOTE_USER([^)]*) = admin\>'
ANSIBLE_REMOTE_USER=administrator ansible-config dump| grep 'DEFAULT_REMOTE_USER([^)]*) = administrator\>'
ansible-config list | grep 'DEFAULT_REMOTE_USER'

# Collection
ansible-config view -c ./ansible-testé.cfg | grep 'collections_paths = /tmp/collections'
ansible-config dump -c ./ansible-testé.cfg | grep 'COLLECTIONS_PATHS([^)]*) ='
ANSIBLE_COLLECTIONS_PATHS=/tmp/collections ansible-config dump| grep 'COLLECTIONS_PATHS([^)]*) ='
ansible-config list | grep 'COLLECTIONS_PATHS'

# 'view' command must fail when config file is missing or has an invalid file extension
ansible-config view -c ./ansible-non-existent.cfg 2> err1.txt || grep -Eq 'ERROR! The provided configuration file is missing or not accessible:' err1.txt || (cat err*.txt; rm -f err1.txt; exit 1)
ansible-config view -c ./no-extension 2> err2.txt || grep -q 'Unsupported configuration file extension' err2.txt || (cat err2.txt; rm -f err*.txt; exit 1)
rm -f err*.txt

# test setting playbook_dir via envvar
ANSIBLE_PLAYBOOK_DIR=/doesnotexist/tmp ansible localhost -m debug -a var=playbook_dir | grep '"playbook_dir": "/doesnotexist/tmp"'

# test setting playbook_dir via cmdline
ansible localhost -m debug -a var=playbook_dir --playbook-dir=/doesnotexist/tmp | grep '"playbook_dir": "/doesnotexist/tmp"'

# test setting playbook dir via ansible.cfg
env -u ANSIBLE_PLAYBOOK_DIR ANSIBLE_CONFIG=./playbookdir_cfg.ini ansible localhost -m debug -a var=playbook_dir | grep '"playbook_dir": "/doesnotexist/tmp"'

# test adhoc callback triggers
ANSIBLE_STDOUT_CALLBACK=callback_debug ANSIBLE_LOAD_CALLBACK_PLUGINS=1 ansible --playbook-dir . testhost -i ../../inventory -m ping | grep -E '^v2_' | diff -u adhoc-callback.stdout -

# CB_WANTS_IMPLICIT isn't anything in Ansible itself.
# Our test cb plugin just accepts it. It lets us avoid copypasting the whole
# plugin just for two tests.
CB_WANTS_IMPLICIT=1 ANSIBLE_STDOUT_CALLBACK=callback_meta ANSIBLE_LOAD_CALLBACK_PLUGINS=1 ansible-playbook -i ../../inventory --extra-vars @./vars.yml playbook.yml | grep 'saw implicit task'

set +e
if ANSIBLE_STDOUT_CALLBACK=callback_meta ANSIBLE_LOAD_CALLBACK_PLUGINS=1 ansible-playbook -i ../../inventory --extra-vars @./vars.yml playbook.yml | grep 'saw implicit task'; then
  echo "Callback got implicit task and should not have"
  exit 1
fi
set -e

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

# Ensure extra vars filename is prepended with '@' sign
if ansible-playbook -i ../../inventory --extra-vars /tmp/non-existing-file playbook.yml; then
    echo "extra_vars filename without '@' sign should cause failure"
    exit 1
fi

# Ensure extra vars filename is prepended with '@' sign
if ansible-playbook -i ../../inventory --extra-vars ./vars.yml playbook.yml; then
    echo "extra_vars filename without '@' sign should cause failure"
    exit 1
fi

ansible-playbook -i ../../inventory --extra-vars @./vars.yml playbook.yml
