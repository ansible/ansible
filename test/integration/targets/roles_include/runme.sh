#!/usr/bin/env bash

set -eux

ARGSPEC="Validating arguments against arg spec 'main'"

# A full run executes every role in roles_include.
[ "$(ansible-playbook test_roles_include.yml -i ../../inventory "$@" | grep -c '"msg": "WEB"')" = "1" ]
[ "$(ansible-playbook test_roles_include.yml -i ../../inventory "$@" | grep -c '"msg": "DB"')" = "1" ]

# A tag-scoped run loads only the selected role. roles_include resolves roles
# dynamically, so an unselected role is never loaded: its tasks do not run AND
# its automatic argument-spec validation never happens.
out="$(ansible-playbook test_roles_include.yml -i ../../inventory --tags web "$@")"
[ "$(grep -c '"msg": "WEB"' <<<"$out")" = "1" ]
[ "$(grep -c '"msg": "DB"' <<<"$out")" = "0" ]
[ "$(grep -c "$ARGSPEC" <<<"$out")" = "0" ]

# Contrast: the static roles: keyword still loads the unselected role under the
# same filter, so its arg-spec validation (tagged 'always') runs regardless.
out_static="$(ansible-playbook test_roles_static.yml -i ../../inventory --tags web "$@")"
[ "$(grep -c '"msg": "WEB"' <<<"$out_static")" = "1" ]
[ "$(grep -c '"msg": "DB"' <<<"$out_static")" = "0" ]
[ "$(grep -c "$ARGSPEC" <<<"$out_static")" = "1" ]

echo "roles_include integration tests passed"
