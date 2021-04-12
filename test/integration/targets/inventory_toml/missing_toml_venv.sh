#!/usr/bin/env bash

set -eux

# Virtualenv without toml, to ensure the toml plugin throws properly.
source virtualenv-isolated.sh

# And install enough deps in the venv to run ansible...
pip install --upgrade pip
pip install -r $OUTPUT_DIR/../../../../requirements.txt -c $OUTPUT_DIR/../../../lib/ansible_test/_data/requirements/constraints.txt --disable-pip-version-check

# This should never be installed in the isolated venv, but just to be safe...
pip list | grep '^toml\W' && pip uninstall -y toml

missing_toml="$(ansible -i test1.toml -m ping all -vvv 2>&1)"
grep -q "Failed to parse.*" <<< "$missing_toml"
grep -q ".*TOML inventory plugin requires.*" <<< "$missing_toml"
grep -q "python \"toml\" library" <<< "$missing_toml"

# `deactivate` fails but would probably break ansible-test --venv anyway
# that is why this is in its own script that runs in a subshell.
