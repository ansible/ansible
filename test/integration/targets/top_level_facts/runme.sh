#!/usr/bin/env bash

set -eux

ANSIBLE_DEPRECATION_WARNINGS=1 ansible-playbook loop.yml -i inventory -v "$@" 2>&1 | tee out.txt
grep "INJECT_FACTS_AS_VARS default to \`True\` is deprecated" out.txt

ANSIBLE_DEPRECATION_WARNINGS=1 ansible-playbook delegate_to.yml -i inventory -v "$@" 2>&1 | tee out.txt
grep -v "INJECT_FACTS_AS_VARS default to \`True\` is deprecated" out.txt
