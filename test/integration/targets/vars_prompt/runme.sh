#!/usr/bin/env bash

set -eux

# Interactively test vars_prompt
python test-vars_prompt.py -i ../../inventory "$@"
