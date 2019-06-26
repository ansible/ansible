#!/usr/bin/env bash

function cleanup {
    rm -f ${PLUGIN_VARS_LOG_PATH}
}
trap cleanup EXIT

function clear_log {
    truncate --size=0 ${PLUGIN_VARS_LOG_PATH}
}
function fill_template {
    sed "s#PLAY_DIR#$PLAY_DIR#;s#INV_DIR#$INV_DIR#" $1
}

function fail {
    echo --- >&2
    echo Full log: >&2
    cat ${PLUGIN_VARS_LOG_PATH} >&2
    echo --- >&2
    let EXIT_CODE++
}

PLAY_DIR=${PWD}
EXIT_CODE=

export PLUGIN_VARS_LOG_PATH=$(mktemp)

for ANSIBLE_CONFIG in configs/* ; do
    export ANSIBLE_CONFIG
    LOG_NAME=$(basename -s .cfg ${ANSIBLE_CONFIG}).log

    ## inventory dir == playbook dir
    INV_DIR=${PWD}
    echo CONFIG: ${ANSIBLE_CONFIG} INVENTORY: ${INV_DIR}/inventory

    clear_log
    ansible-playbook playbook.yml -i inventory > /dev/null

    TEMPLATE=logs/inventory_next_to_playbook/${LOG_NAME}

    if ! diff ${PLUGIN_VARS_LOG_PATH} <(fill_template ${TEMPLATE}) >&2; then
        fail
    fi

    ## inventory dir != playbook dir
    INV_DIR=$(dirname $(readlink -f inventory))
    echo CONFIG: ${ANSIBLE_CONFIG} INVENTORY: ${INV_DIR}/inventory

    clear_log
    ansible-playbook playbook.yml -i ../../inventory > /dev/null

    TEMPLATE=logs/remote_inventory/${LOG_NAME}

    if ! diff ${PLUGIN_VARS_LOG_PATH} <(fill_template ${TEMPLATE}) >&2; then
        fail
    fi
done

exit ${EXIT_CODE}
