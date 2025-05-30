#!/usr/bin/env bash

set -eux

# run type tests
ansible -a 'sleep 5' --task-timeout 1 localhost |grep 'Timed out after'

# -a parsing with json
ansible --task-timeout 5 localhost -m command -a '{"cmd": "whoami"}' | grep 'rc=0'

# ensure that legacy deserializer behaves as expected on JSON CLI args (https://github.com/ansible/ansible/issues/82600)
# also ensure that various templated args function (non-exhaustive)
_ANSIBLE_TEMPLAR_UNTRUSTED_TEMPLATE_BEHAVIOR=warning ansible '{{"localhost"}}' -m '{{"debug"}}' -a var=fromcli -e '{"fromcli":{"no_trust":{"__ansible_unsafe":"{{\"hello\"}}"},"trust":"{{ 1 }}"}}' > "${OUTPUT_DIR}/output.txt" 2>&1
grep '"no_trust": "{{."hello."}}"' "${OUTPUT_DIR}/output.txt"  # ensure that the template was not rendered
grep '"trust": 1' "${OUTPUT_DIR}/output.txt"  # ensure that the trusted template was rendered
grep "Encountered untrusted template" "${OUTPUT_DIR}/output.txt"  # look for the untrusted template warning text

# test ansible --flush-cache
export ANSIBLE_CACHE_PLUGIN=jsonfile
export ANSIBLE_CACHE_PLUGIN_CONNECTION=./
# verify facts are not yet present
ansible localhost -m assert -a '{"that": "ansible_facts.distribution is not defined"}'
# collect and cache facts
ansible localhost -m setup > /dev/null
# verify facts were cached
ansible localhost -m assert -a '{"that": "ansible_facts.distribution is defined"}'
# test flushing the fact cache
ansible --flush-cache localhost -m debug -a "msg={{ ansible_facts }}" | grep '"msg": {}'
