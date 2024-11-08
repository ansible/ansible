#!/usr/bin/env bash

set -eux -o pipefail

export ANSIBLE_DEPRECATION_WARNINGS=True

### check general config

# not using anything deprecated , so no notice
[ "$(ANSIBLE_CONFIG='entry_key_not_deprecated.cfg' ansible -m meta -a 'noop'  localhost 2>&1 | grep -c 'DEPRECATION')" -eq "0" ]

# entry source is deprecated, but entry is not consumed, so no notice
[ "$(ANSIBLE_CONFIG='entry_key_deprecated.cfg' ansible -m meta -a 'noop' localhost 2>&1 | grep -c 'DEPRECATION')" -eq "0" ]

# check for entry source deprecation including the name of the option, consumed so must trigger
[ "$(ANSIBLE_CONFIG='entry_key_deprecated.cfg' ansible -m debug -a 'msg={{q("config", "_Z_TEST_ENTRY")}}' localhost 2>&1 | grep -c "\[DEPRECATION WARNING\]: \[testing\]deprecated option.")" -eq "1" ]

# check deprecated entry is not accessed, so no notice
[ "$(ANSIBLE_CONFIG='entry_key_deprecated2.cfg' ansible -m meta -a 'noop'  localhost 2>&1 | grep -c 'DEPRECATION')" -eq "0" ]

# check deprecated entry, consumed so must trigger
[ "$(ANSIBLE_TEST_ENTRY2=1 ansible -m debug -a 'msg={{q("config", "_Z_TEST_ENTRY_2")}}' localhost  2>&1 | grep -c 'DEPRECATION')" -eq "1" ]


### check plugin config

# force use of the test plugin
export ANSIBLE_CACHE_PLUGIN_CONNECTION=/var/tmp
export ANSIBLE_CACHE_PLUGIN=notjsonfile

# check for plugin(s) config option and setting non deprecation
[ "$(ANSIBLE_CACHE_PLUGIN_TIMEOUT=1 ansible -m meta -a 'noop'  localhost --playbook-dir ./ 2>&1 | grep -c 'DEPRECATION')" -eq "0" ]

# check for plugin(s) config option setting deprecation
[ "$(ANSIBLE_NOTJSON_CACHE_PLUGIN_TIMEOUT=1 ansible -m meta -a 'noop'  localhost --playbook-dir ./ 2>&1 | grep -c 'DEPRECATION')" -eq "1" ]

# check for plugin(s) config option deprecation
[ "$(ANSIBLE_NOTJSON_CACHE_PLUGIN_REMOVEME=1 ansible -m meta -a 'noop'  localhost --playbook-dir ./ 2>&1 | grep -c 'DEPRECATION')" -eq "1" ]

# check for the module deprecation
[ "$(ansible-doc willremove --playbook-dir ./ | grep -c 'DEPRECATED')" -eq "1" ]

# check for the module option deprecation
[ "$(ansible-doc removeoption --playbook-dir ./ | grep -c 'deprecated:')" -eq "1" ]

# check for plugin deprecation
[ "$(ansible-doc -t cache notjsonfile --playbook-dir ./ | grep -c 'DEPRECATED:')" -eq "1" ]
