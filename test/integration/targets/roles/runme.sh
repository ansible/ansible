#!/usr/bin/env bash

set -eux

# test no dupes when dependencies in b and c point to a in roles:
[ "$(ansible-playbook no_dupes.yml -i ../../inventory --tags inroles "$@" | grep '"msg": "A"' |wc -l)" = "1" ]
[ "$(ansible-playbook no_dupes.yml -i ../../inventory --tags acrossroles "$@" | grep '"msg": "A"' |wc -l)" = "1" ]

# but still dupe across plays
[ "$(ansible-playbook no_dupes.yml -i ../../inventory "$@" | grep '"msg": "A"' |wc -l)" = "2" ]

# include/import can execute another instance of role
[ "$(ansible-playbook allowed_dupes.yml -i ../../inventory --tags importrole "$@" | grep '"msg": "A"' |wc -l)" = "2" ]
[ "$(ansible-playbook allowed_dupes.yml -i ../../inventory --tags includerole "$@" | grep '"msg": "A"' |wc -l)" = "2" ]
