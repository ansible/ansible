#!/usr/bin/env bash

set -eux

# Temporary hack for PEP 668 on newer systems.
# Remove once ansible-test can provide targets their own virtual environment.
# Tests which can manage their own virtual environment should not use this approach.
export PIP_BREAK_SYSTEM_PACKAGES=1

# Requirements have to be installed prior to running ansible-playbook
# because plugins and requirements are loaded before the task runs
python -m pip install passlib
