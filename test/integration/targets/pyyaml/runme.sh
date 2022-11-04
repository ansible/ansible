#!/usr/bin/env bash

set -eu -o pipefail
source virtualenv.sh
set +x

# deps are already installed, using --no-deps to avoid re-installing them
# Install PyYAML without libyaml to validate ansible can run
PYYAML_FORCE_LIBYAML=0 pip install --no-binary PyYAML --ignore-installed --no-cache-dir --no-deps PyYAML

ansible --version | tee /dev/stderr | grep 'libyaml = False'
