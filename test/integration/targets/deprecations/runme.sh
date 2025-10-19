#!/usr/bin/env bash

set -eux -o pipefail

export ANSIBLE_DEPRECATION_WARNINGS=False

ansible-playbook deprecated.yml -i ../../inventory "${@}" 2>&1 | tee disabled.txt

grep "This is a warning" disabled.txt  # should be visible

if grep "DEPRECATION" disabled.txt; then
  echo "ERROR: deprecation warnings should not be visible"
  exit 1
fi

export ANSIBLE_DEPRECATION_WARNINGS=True

ansible-playbook deprecated.yml -i ../../inventory "${@}"

### check general config

# check for entry key valid, no deprecation
[ "$(ANSIBLE_CONFIG='entry_key_not_deprecated.cfg' ansible -m meta -a 'noop'  localhost 2>&1 | grep -c 'DEPRECATION')" -eq "0" ]

# check for entry key deprecation including the name of the option, must be defined to trigger
[ "$(ANSIBLE_CONFIG='entry_key_deprecated.cfg' ansible -m meta -a 'noop' localhost 2>&1 | grep -c "\[DEPRECATION WARNING\]: \[testing\]deprecated option.")" -eq "1" ]

# DTFIX: fix issue with x2 deprecation and wrong pllugin attribution
# check for deprecation of entry itself, must be consumed to trigger
[ "$(ANSIBLE_TEST_ENTRY2=1 ansible -m debug -a 'msg={{q("config", "_Z_TEST_ENTRY_2")}}' localhost  2>&1 | grep -c 'DEPRECATION')" -eq "2" ]

# check for entry deprecation, just need key defined to trigger
[ "$(ANSIBLE_CONFIG='entry_key_deprecated2.cfg' ansible -m meta -a 'noop'  localhost 2>&1 | grep -c 'DEPRECATION')" -eq "1" ]


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

# Injection default is deprecated
[ "$(ANSIBLE_INJECT_FACT_VARS=1 ansible-playbook injectfacts.yml 2>&1 | grep -c 'INJECT_FACTS_AS_VARS')" -eq "0" ]
