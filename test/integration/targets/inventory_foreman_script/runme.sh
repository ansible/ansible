#!/usr/bin/env bash

set -euo pipefail

export FOREMAN_HOST="${FOREMAN_HOST:-localhost}"
export FOREMAN_PORT="${FOREMAN_PORT:-8080}"
export FOREMAN_INI_PATH="${OUTPUT_DIR}/foreman.ini"


############################################
#   SMOKETEST WITH SIMPLE INI
############################################

cat > "$FOREMAN_INI_PATH" <<FOREMAN_INI
[foreman]
url = http://${FOREMAN_HOST}:${FOREMAN_PORT}
user = ansible-tester
password = secure
ssl_verify = False
FOREMAN_INI

# use ansible to validate the return data
ansible-playbook -i foreman.sh test_foreman_inventory.yml --connection=local
RC=$?
if [[ $RC != 0 ]]; then
    echo "foreman inventory script smoketest failed"
    exit $RC
fi

############################################
#   SMOKETEST WITH NON-ASCII INI
############################################

cat > "$FOREMAN_INI_PATH" <<FOREMAN_INI
[foreman]
url = http://${FOREMAN_HOST}:${FOREMAN_PORT}
user = ansible-tester
password = secure
ssl_verify = False
group_prefix = Ľuboš_
FOREMAN_INI

# use ansible to validate the return data
ansible-playbook -i foreman.sh test_foreman_inventory.yml --connection=local
RC=$?
if [[ $RC != 0 ]]; then
    echo "foreman inventory script non-ascii failed"
    exit $RC
fi
