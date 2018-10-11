#!/usr/bin/env bash

[[ -n "$DEBUG" || -n "$ANSIBLE_DEBUG" ]] && set -x

set -euo pipefail

export ANSIBLE_CONFIG=ansible.cfg
export FOREMAN_HOST="${FOREMAN_HOST:-localhost}"
export FOREMAN_PORT="${FOREMAN_PORT:-8080}"
FOREMAN_CONFIG=foreman.ini

# flag for checking whether cleanup has already fired
_is_clean=

function _cleanup() {
    [[ -n "$_is_clean" ]] && return  # don't double-clean
    echo Cleanup: removing $FOREMAN_CONFIG...
    rm -vf "$FOREMAN_CONFIG"
    echo Cleanup: removing foreman.py...
    rm -v foreman.py
    echo Cleanup: removing inventory.json...
    rm -vf inventory.json
    unset ANSIBLE_CONFIG
    unset FOREMAN_HOST
    unset FOREMAN_PORT
    unset FOREMAN_CONFIG
    _is_clean=1
}
trap _cleanup INT TERM EXIT

cat > "$FOREMAN_CONFIG" <<FOREMAN_YAML
[foreman]
url = http://${FOREMAN_HOST}:${FOREMAN_PORT}
user = ansible-tester
password = secure
ssl_verify = False
FOREMAN_YAML

cp ~/ansible/contrib/inventory/foreman.py .
# run once to opcheck and validate script
./foreman.py | tee -a inventory.json
# use ansible to validate the return data
ansible-playbook -i foreman.py test_foreman_inventory.yml --connection=local
