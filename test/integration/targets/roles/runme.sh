#!/usr/bin/env bash

set -eux

# test no dupes when dependencies in b and c point to a in roles:
[ "$(ansible-playbook no_dupes.yml -i ../../inventory --tags inroles "$@" | grep -c '"msg": "A"')" = "1" ]
[ "$(ansible-playbook no_dupes.yml -i ../../inventory --tags acrossroles "$@" | grep -c '"msg": "A"')" = "1" ]
[ "$(ansible-playbook no_dupes.yml -i ../../inventory --tags intasks "$@" | grep -c '"msg": "A"')" = "1" ]

# but still dupe across plays
[ "$(ansible-playbook no_dupes.yml -i ../../inventory "$@" | grep -c '"msg": "A"')" = "3" ]

# and don't dedupe before the role successfully completes
[ "$(ansible-playbook role_complete.yml -i ../../inventory -i fake, --tags conditional_skipped "$@" | grep -c '"msg": "A"')" = "1" ]
[ "$(ansible-playbook role_complete.yml -i ../../inventory -i fake, --tags conditional_failed "$@" | grep -c '"msg": "failed_when task succeeded"')" = "1" ]
[ "$(ansible-playbook role_complete.yml -i ../../inventory -i fake, --tags unreachable "$@" | grep -c '"data": "reachable"')" = "1" ]
ansible-playbook role_complete.yml -i ../../inventory -i fake, --tags unreachable "$@" | grep -e 'ignored=2'

# include/import can execute another instance of role
[ "$(ansible-playbook allowed_dupes.yml -i ../../inventory --tags importrole "$@" | grep -c '"msg": "A"')" = "2" ]
[ "$(ansible-playbook allowed_dupes.yml -i ../../inventory --tags includerole "$@" | grep -c '"msg": "A"')" = "2" ]

[ "$(ansible-playbook dupe_inheritance.yml -i ../../inventory "$@" | grep -c '"msg": "abc"')" = "3" ]

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

# ensure vars scope is correct
ansible-playbook vars_scope.yml -i ../../inventory "$@"

# test nested includes get parent roles greater than a depth of 3
[ "$(ansible-playbook 47023.yml -i ../../inventory "$@" | grep '\<\(Default\|Var\)\>' | grep -c 'is defined')" = "2" ]

# ensure import_role called from include_role has the include_role in the dep chain
ansible-playbook role_dep_chain.yml -i ../../inventory "$@"
