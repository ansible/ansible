#!/usr/bin/env bash

set -eux

# check if we get proper json error
ansible-playbook -i ../../inventory attempt_to_load_invalid_json.yml "$@" 2>&1|grep 'JSON:'

trap 'rm -f actually_yaml.py out-py out-yaml' EXIT

# equivalent Python and YAML should yield same result
ansible-playbook main.py -i ../../inventory | tee out-py
ansible-playbook main.yml -i ../../inventory | tee out-yaml
diff -u out-py out-yaml

# Historically, all files, including *.py, have been loaded as YAML. In the
# initial version of Python playbook support, if a .py file fails to import, a
# warning message is emitted and the historical YAML loading is still
# attempted. Erroring out immediately in the future seems simpler, but the path
# of abundant caution probably includes deprecation warnings and reserving the
# change for a major version bump.
cp main.yml actually_yaml.py
ansible-playbook actually_yaml.py -i ../../inventory | tee out-yaml
for i in 1 2 3; do
  grep "ok: \[localhost\] => (item=$i)" out-yaml
  grep "\"item\": $i" out-yaml
done
