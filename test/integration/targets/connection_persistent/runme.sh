#!/usr/bin/env bash

set -eux

helper_counter_path="$(mktemp)"
alias_helper_counter_path="$(mktemp)"
legacy_helper_counter_path="$(mktemp)"
trap 'rm -f "${helper_counter_path}" "${alias_helper_counter_path}" "${legacy_helper_counter_path}"' EXIT

export ANSIBLE_TEST_CONNECTION_HELPER_COUNTER="${helper_counter_path}"
export ANSIBLE_TEST_REAL_CONNECTION_PATH="${_ANSIBLE_CONNECTION_PATH:-}"
export _ANSIBLE_CONNECTION_PATH="${PWD}/connection_helper_wrapper.py"
unset ANSIBLE_TEST_CONNECTION_HELPER_TARGET

ansible-playbook -i inventory playbook.yml -v -e "helper_counter_path=${helper_counter_path}" "$@"

export ANSIBLE_TEST_CONNECTION_HELPER_COUNTER="${alias_helper_counter_path}"
export ANSIBLE_TEST_CONNECTION_HELPER_BARRIER_SIZE=2

ansible-playbook -i inventory aliases.yml -v -e "alias_helper_counter_path=${alias_helper_counter_path}" "$@"

export ANSIBLE_TEST_CONNECTION_HELPER_COUNTER="${legacy_helper_counter_path}"
export ANSIBLE_TEST_CONNECTION_HELPER_TARGET="${PWD}/legacy_connection_helper.py"
unset ANSIBLE_TEST_CONNECTION_HELPER_BARRIER_SIZE

ansible-playbook -i inventory legacy_fallback.yml -v -e "legacy_helper_counter_path=${legacy_helper_counter_path}" "$@"
