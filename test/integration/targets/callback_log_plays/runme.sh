#!/usr/bin/env bash

set -eux

export ANSIBLE_CALLBACK_WHITELIST="log_plays,${ANSIBLE_CALLBACK_WHITELIST:-}"

# run play, should create log and dir if needed
export ANSIBLE_LOG_FOLDER="logit"
ansible-playbook ping_log.yml -v "$@"
[[ -f "${ANSIBLE_LOG_FOLDER}/localhost" ]]

# now force it to fail
export ANSIBLE_LOG_FOLDER="logit.file"
touch "${ANSIBLE_LOG_FOLDER}"
ansible-playbook ping_log.yml -v "$@" 2>&1| grep 'Failure using method (v2_runner_on_ok) in callback plugin'
[[ ! -f "${ANSIBLE_LOG_FOLDER}/localhost" ]]
