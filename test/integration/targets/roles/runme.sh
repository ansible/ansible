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


# ensure role vars are inherited correctly
ANSIBLE_PRIVATE_ROLE_VARS=True ansible-playbook 39543.yml -i ../../inventory "$@" | tee out.txt
test "$(grep '"msg": "role1"' -c out.txt)" = "1"
test "$(grep '"msg": "role2"' -c out.txt)" = "1"
test "$(grep '"msg": "role3"' -c out.txt)" = "0"


# test nested includes get parent roles greater than a depth of 3
[ "$(ansible-playbook 47023.yml -i ../../inventory "$@" | grep '\<\(Default\|Var\)\>' | grep -c 'is defined')" = "2" ]
