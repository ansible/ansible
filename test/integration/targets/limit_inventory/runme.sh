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

# Intersection patterns with limits
ansible -i hosts.yml all --limit '&host1' --list-hosts | tee out ; grep -q 'hosts (1)' out

# Multiple negations
ansible -i hosts.yml all --limit '!host1:!host2' --list-hosts | tee out ; grep -q 'hosts (1)' out
ansible -i hosts.yml all --limit '!host1,!host2' --list-hosts | tee out ; grep -q 'hosts (1)' out

# Negation-only limit with 'all' pattern (shouldn't add implicit localhost)
ansible -i hosts.yml all --limit '!host2' --list-hosts | tee out ; grep -q 'hosts (2)' out

# ensure implicit localhost available with limits when explicitly in play pattern
ansible-playbook -i hosts.yml --limit '!host2' include_localhost.yml

# Explicitly excluding localhost should work when inventory has explicit localhost
ansible-playbook -i hosts_with_localhost.yml --limit '!localhost' exclude_localhost.yml

# localhost-only play with non-localhost limit should still include localhost
ansible -i hosts.yml localhost --limit 'host1' --list-hosts | tee out ; grep -q 'hosts (1)' out
