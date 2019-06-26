#!/usr/bin/env bash

function cleanup {
    rm -f "$PLUGIN_VARS_LOG_PATH"
}
trap cleanup EXIT

function new_log {
    cleanup
    PLUGIN_VARS_LOG_PATH=$(mktemp)
    export PLUGIN_VARS_LOG_PATH
}
function fill_template {
    sed "s#PLAY_DIR#$PLAY_DIR#;s#INV_DIR#$INV_DIR#" "$1"
}

function fail {
    echo --- >&2
    echo Full log: >&2
    cat "$PLUGIN_VARS_LOG_PATH" >&2
    echo --- >&2
    let EXIT_CODE++
}

PLAY_DIR="/test/integration/targets/plugin_vars_once"
EXIT_CODE=0

PLUGIN_VARS_LOG_PATH=

CASES="
default
no_inventory
no_play
no_plugins
reverse
reverse_no_inventory
reverse_no_play
"

for CASE in ${CASES}; do
    ANSIBLE_CONFIG="configs/$CASE.cfg"
    export ANSIBLE_CONFIG
    LOG_NAME="$CASE.log"

    ## inventory dir == playbook dir
    INV_DIR="$PLAY_DIR"
    echo CONFIG: "$ANSIBLE_CONFIG" INVENTORY: "$INV_DIR"/inventory >&2

    new_log
    ansible-playbook playbook.yml -i inventory "$@"

    TEMPLATE=logs/inventory_next_to_playbook/"$LOG_NAME"

    if ! diff "$PLUGIN_VARS_LOG_PATH" <(fill_template "$TEMPLATE") >&2; then
        fail
    fi

    ## inventory dir != playbook dir
    INV_DIR="/test/integration"
    echo CONFIG: "$ANSIBLE_CONFIG" INVENTORY: "$INV_DIR"/inventory >&2

    new_log
    ansible-playbook playbook.yml -i ../../inventory "$@"

    TEMPLATE=logs/remote_inventory/"$LOG_NAME"

    if ! diff "$PLUGIN_VARS_LOG_PATH" <(fill_template "$TEMPLATE") >&2; then
        fail
    fi
done

exit "$EXIT_CODE"
