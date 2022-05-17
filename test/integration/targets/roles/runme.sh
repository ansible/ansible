#!/usr/bin/env bash

set -eux

# test no dupes when dependencies in b and c point to a in roles:
[ "$(ansible-playbook no_dupes.yml -i ../../inventory --tags inroles "$@" | grep -c '"msg": "A"')" = "1" ]
[ "$(ansible-playbook no_dupes.yml -i ../../inventory --tags acrossroles "$@" | grep -c '"msg": "A"')" = "1" ]
[ "$(ansible-playbook no_dupes.yml -i ../../inventory --tags intasks "$@" | grep -c '"msg": "A"')" = "1" ]

# but still dupe across plays
[ "$(ansible-playbook no_dupes.yml -i ../../inventory "$@" | grep -c '"msg": "A"')" = "3" ]

# include/import can execute another instance of role
[ "$(ansible-playbook allowed_dupes.yml -i ../../inventory --tags importrole "$@" | grep -c '"msg": "A"')" = "2" ]
[ "$(ansible-playbook allowed_dupes.yml -i ../../inventory --tags includerole "$@" | grep -c '"msg": "A"')" = "2" ]


# ensure role data is merged correctly
ansible-playbook data_integrity.yml -i ../../inventory "$@"

# ensure role fails when trying to load 'non role' in  _from
ansible-playbook no_outside.yml -i ../../inventory "$@" > role_outside_output.log 2>&1 || true
if grep "as it is not inside the expected role path" role_outside_output.log >/dev/null; then
  echo "Test passed (playbook failed with expected output, output not shown)."
else
  echo "Test failed, expected output from playbook failure is missing, output not shown)."
  exit 1
fi
