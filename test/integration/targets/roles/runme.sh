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
ansible-playbook no_outside.yml -i ../../inventory "$@" 2>&1 > role_outside_output.log || true
if grep "as it is not inside the expected role path" output.log >/dev/null; then
  echo "Test passed (playbook failed with expected output, output not shown)."
  exit 0
fi
rm role_outside_output.log
