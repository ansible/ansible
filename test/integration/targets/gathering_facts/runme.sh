#!/usr/bin/env bash

set -eux

## ANSIBLE_CACHE_PLUGINS=cache_plugins/ ANSIBLE_CACHE_PLUGIN=none ansible-playbook test_gathering_facts.yml -i inventory -v "$@"
#ansible-playbook test_gathering_facts.yml -i inventory -v "$@"
## ANSIBLE_CACHE_PLUGIN=base ansible-playbook test_gathering_facts.yml -i inventory -v "$@"
#
#ANSIBLE_GATHERING=smart ansible-playbook test_run_once.yml -i inventory -v "$@"
#
## ensure clean_facts is working properly
#ansible-playbook test_prevent_injection.yml -i inventory -v "$@"


export ANSIBLE_NOCOLOR=true ANSIBLE_FORCE_COLOR=false
# ensure fact gathering merge order is expected:
ansible -m gather_facts -e 'ansible_facts_modules=facts_one,facts_two' localhost --playbook-dir ./ > one_two.current
diff -u one_two.output one_two.current

# now reverse order
ansible -m gather_facts -e 'ansible_facts_modules=facts_two,facts_one' localhost --playbook-dir ./ > two_one.current
diff -u two_one.output two_one.current
