#!/usr/bin/env bash

set -eux

# test no dupes when dependencies in b and c point to a in roles:
[ "$(ansible-playbook no_dupes.yml -i ../../inventory --tags inroles "$@" | grep -c '"msg": "A"')" = "1" ]
[ "$(ansible-playbook no_dupes.yml -i ../../inventory --tags acrossroles "$@" | grep -c '"msg": "A"')" = "1" ]

# but still dupe across plays
[ "$(ansible-playbook no_dupes.yml -i ../../inventory "$@" | grep -c '"msg": "A"')" = "2" ]

# include/import can execute another instance of role
[ "$(ansible-playbook allowed_dupes.yml -i ../../inventory --tags importrole "$@" | grep -c '"msg": "A"')" = "2" ]
[ "$(ansible-playbook allowed_dupes.yml -i ../../inventory --tags includerole "$@" | grep -c '"msg": "A"')" = "2" ]


# ensure role data is merged correctly
ansible-playbook data_integrity.yml -i ../../inventory "$@"


# ensure role vars are inherited correctly
ANSIBLE_PRIVATE_ROLE_VARS=True ANSIBLE_ROLES_PATH=./moar_roles ansible-playbook test_role_parents.yml -i ../../inventory "$@" | tee out.txt
test "$(grep '"msg": "RoleA"' -c out.txt)" = "1"
test "$(grep '"msg": "RoleB"' -c out.txt)" = "1"
test "$(grep '"msg": "RoleC"' -c out.txt)" = "0"
