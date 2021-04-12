#!/usr/bin/env bash

set -eux

# Virtualenv without toml
source virtualenv-isolated.sh

# And install enough deps in the venv to run ansible...
pip install --upgrade pip
pip install -r $OUTPUT_DIR/../../../../requirements.txt -c $OUTPUT_DIR/../../../lib/ansible_test/_data/requirements/constraints.txt --disable-pip-version-check

# This should never be installed in the isolated venv, but just to be safe...
pip list | grep '^toml\W' && pip uninstall -y toml

# And install an old toml
pip install 'toml<0.10'

adhoc="$(ansible -i test1.toml -m ping --connection=local -e ansible_python_interpreter="{{ ansible_playbook_python }}" all -v)"

for i in $(seq -f '%03g' 1 4); do
    grep -qE "local${i} \| SUCCESS.*\"ping\": \"pong\"" <<< "$adhoc"
done

ansible_inventory="$(ansible-inventory -i test1.toml --list)"
grep -q "\"local004\": {" <<< "$ansible_inventory"

ansible_inventory_toml="$(ansible-inventory -i test1.toml --list --toml)"
grep -q "\[mygroup.hosts.local001\]" <<< "$ansible_inventory_toml"
grep -q "ansible_connection = \"local\"" <<< "$ansible_inventory_toml"

# `deactivate` fails but would probably break ansible-test --venv anyway
# that is why this is in its own script that runs in a subshell.
