#!/usr/bin/env bash
# Aggregate code coverage results for later processing.

set -o pipefail -eu

agent_temp_directory="$1"

PATH="${PWD}/bin:${PATH}"

mkdir "${agent_temp_directory}/coverage/"

options=(--venv --venv-system-site-packages --color -v)

ansible-test coverage combine --export "${agent_temp_directory}/coverage/" "${options[@]}"
ansible-test coverage analyze targets generate "${agent_temp_directory}/coverage/coverage-analyze-targets.json" "${options[@]}"
