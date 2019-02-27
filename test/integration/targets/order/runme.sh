#!/usr/bin/env bash

set -eux

for EXTRA in '{"inputlist": ["hostB", "hostA", "hostD", "hostC"]}' \
             '{"myorder": "inventory", "inputlist": ["hostB", "hostA", "hostD", "hostC"]}' \
             '{"myorder": "sorted", "inputlist": ["hostA", "hostB", "hostC", "hostD"]}'  \
		     '{"myorder": "reverse_sorted", "inputlist": ["hostD", "hostC", "hostB", "hostA"]}' \
             '{"myorder": "reverse_inventory", "inputlist": ["hostC", "hostD", "hostA", "hostB"]}'
do
	rm shostlist.txt hostlist.txt || true
	ansible-playbook order.yml --forks 1 -i inventory -e "$EXTRA" "$@"
done
