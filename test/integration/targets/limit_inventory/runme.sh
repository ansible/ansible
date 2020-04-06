#!/usr/bin/env bash

set -eux

trap 'echo "Host pattern limit test failed"' ERR

# https://github.com/ansible/ansible/issues/61964

# These tests should return all hosts
ansible -i hosts.yml all --limit ,, --list-hosts | tee out ; grep -q 'hosts (3)' out
ansible -i hosts.yml ,, --list-hosts | tee out ; grep -q 'hosts (3)' out
ansible -i hosts.yml , --list-hosts | tee out ; grep -q 'hosts (3)' out
ansible -i hosts.yml all --limit , --list-hosts | tee out ; grep -q 'hosts (3)' out
ansible -i hosts.yml all --limit '' --list-hosts | tee out ; grep -q 'hosts (3)' out


# Only one host
ansible -i hosts.yml all --limit ,,host1 --list-hosts | tee out ; grep -q 'hosts (1)' out
ansible -i hosts.yml ,,host1 --list-hosts | tee out ; grep -q 'hosts (1)' out

ansible -i hosts.yml all --limit host1,, --list-hosts | tee out ; grep -q 'hosts (1)' out
ansible -i hosts.yml host1,, --list-hosts | tee out ; grep -q 'hosts (1)' out


# Only two hosts
ansible -i hosts.yml all --limit host1,,host3 --list-hosts | tee out ; grep -q 'hosts (2)' out
ansible -i hosts.yml host1,,host3 --list-hosts | tee out ; grep -q 'hosts (2)' out

ansible -i hosts.yml all --limit 'host1, ,    ,host3' --list-hosts | tee out ; grep -q 'hosts (2)' out
ansible -i hosts.yml 'host1, ,    ,host3' --list-hosts | tee out ; grep -q 'hosts (2)' out

