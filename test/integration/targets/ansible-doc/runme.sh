#!/usr/bin/env bash

set -eux -o pipefail

ansible-doc --version
ansible-doc --help

declare -a PLUGIN_TYPES=('cache' 'callback' 'connection' 'shell' 'module' 'module_utils' 'ps_module_utils' 'lookup' 'filter' 'test' 'strategy' 'terminal' 'vars' 'cliconf' 'netconf' 'inventory')
echo "${PLUGIN_TYPES[@]}"

for i in "${PLUGIN_TYPES[@]}"
do
    # list plugins of each type
    ansible-doc -t "${i}" -l
    # list plugins of each type and show plugin file location
    ansible-doc -t "${i}" -F
done

# test -l and -l -F without a plugin type, default to 'module'
ansible-doc -l
ansible-doc -F

declare -a MODULES_TO_TEST=('ping' 'copy' 'synchronize')

for i in "${MODULES_TO_TEST[@]}"
do
    # list plugins of each type
    ansible-doc "${i}"
    # list plugins of each type and show plugin file location
    ansible-doc -s "${i}"
done

declare -a CACHE_PLUGINS_TO_TEST=('yaml' 'json' 'redis')
for i in "${CACHE_PLUGINS_TO_TEST[@]}"
do
    # list plugins of each type
    ansible-doc -t cache "${i}"
    # list plugins of each type and show plugin file location
    ansible-doc -t cache -s "${i}"
done

