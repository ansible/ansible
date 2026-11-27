#!/usr/bin/env bash

set -eux

# unknown connection plugins must fail even when inventory overrides the CLI value
for cmd in "ansible-playbook play.yml" "ansible testhost -m ping"; do
    if $cmd -i inventory -c bogus "$@" > out.txt 2>&1; then
        echo "'$cmd -c bogus' unexpectedly succeeded"
        exit 1
    fi
    grep "The connection plugin 'bogus' was not found." out.txt
done

# typo'd --check is parsed as '-c heck' (https://github.com/ansible/ansible/issues/79618)
if ansible-playbook play.yml -i inventory -check "$@" > out.txt 2>&1; then
    echo "'-check' unexpectedly succeeded"
    exit 1
fi
grep "The connection plugin 'heck' was not found." out.txt

# known plugins: short name, FQCN and playbook-adjacent
ansible-playbook play.yml -i inventory -c local "$@"
ansible-playbook play.yml -i inventory -c ansible.builtin.local "$@"
ansible-playbook play.yml -i inventory -c adjacent "$@"
ansible testhost -i inventory -m ping -c ansible.builtin.local "$@"
