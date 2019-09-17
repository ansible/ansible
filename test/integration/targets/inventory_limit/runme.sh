#!/usr/bin/env bash

set -eux

trap 'echo "Host pattern limit test failed"' ERR

# https://github.com/ansible/ansible/issues/61964

# These tests should return all hosts
ansible -i hosts.yml all --limit ,, --list-hosts | grep -q 'hosts (3)'
ansible -i hosts.yml ,, --list-hosts | grep -q 'hosts (3)'
ansible -i hosts.yml , --list-hosts | grep -q 'hosts (3)'
ansible -i hosts.yml all --limit , --list-hosts | grep -q 'hosts (3)'
ansible -i hosts.yml all --limit '' --list-hosts | grep -q 'hosts (3)'


# Only one host
ansible -i hosts.yml all --limit ,,host1 --list-hosts | grep -q 'hosts (1)'
ansible -i hosts.yml ,,host1 --list-hosts | grep -q 'hosts (1)'

ansible -i hosts.yml all --limit host1,, --list-hosts | grep -q 'hosts (1)'
ansible -i hosts.yml host1,, --list-hosts | grep -q 'hosts (1)'


# Only two hosts
ansible -i hosts.yml all --limit host1,,host3 --list-hosts | grep -q 'hosts (2)'
ansible -i hosts.yml host1,,host3 --list-hosts | grep -q 'hosts (2)'

ansible -i hosts.yml all --limit 'host1, ,    ,host3' --list-hosts | grep -q 'hosts (2)'
ansible -i hosts.yml 'host1, ,    ,host3' --list-hosts | grep -q 'hosts (2)'

