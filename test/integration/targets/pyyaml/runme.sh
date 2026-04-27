#!/usr/bin/env bash

set -eu -o pipefail
source virtualenv.sh
set +x

# Verify libyaml is in use.
ansible --version | tee /dev/stderr | grep 'with libyaml'

# Run tests with libyaml.
ansible-playbook runme.yml "${@}"

# deps are already installed, using --no-deps to avoid re-installing them
# Install PyYAML without libyaml to validate ansible can run
PYYAML_FORCE_LIBYAML=0 pip install --no-binary PyYAML --ignore-installed --no-cache-dir --no-deps PyYAML

# Verify libyaml is not in use.
ansible --version | tee /dev/stderr | grep 'without libyaml'

# Run tests without libyaml.
ansible-playbook runme.yml "${@}"
