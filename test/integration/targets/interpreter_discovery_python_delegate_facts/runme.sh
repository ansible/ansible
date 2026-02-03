#!/usr/bin/env bash

set -eux

out="$(ansible-playbook delegate_facts.yml -vvv -i inventory "$@")"

[ "$(grep -c "Attempting python interpreter discovery" <<< "$out")" -eq 1 ]
