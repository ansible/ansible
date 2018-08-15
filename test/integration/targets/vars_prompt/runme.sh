#!/usr/bin/env bash

set -eux

# Install passlib on RHEL and FreeBSD
dist=$(python -c 'import platform; print(platform.dist()[0])')
system=$(python -c 'import platform; print(platform.system())')

if [[ "$dist" == "redhat" || "$system" == "FreeBSD" ]]; then
    pip install passlib
fi

# Interactively test vars_prompt
pip install pexpect
python test-vars_prompt.py -i ../../inventory "$@"
