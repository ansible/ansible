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

# test that dependencies defined under install_dependencies are not executed
[ "$(ansible-playbook install_dependencies.yml --tags role -i ../../inventory "$@" | grep -c '"msg": "A"')" = "0" ]
[ "$(ansible-playbook install_dependencies.yml --tags import_role -i ../../inventory "$@" | grep -c '"msg": "A"')" = "0" ]
[ "$(ansible-playbook install_dependencies.yml --tags include_role -i ../../inventory "$@" | grep -c '"msg": "A"')" = "0" ]
