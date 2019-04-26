#!/usr/bin/env bash

set -eux

cleanup () {
    files="shostlist.txt hostlist.txt"
    for file in $files; do
        if [[ -f "$file" ]]; then
            rm -f "$file"
        fi
    done
}

for EXTRA in '{"inputlist": ["hostB", "hostA", "hostD", "hostC"]}' \
             '{"myorder": "inventory", "inputlist": ["hostB", "hostA", "hostD", "hostC"]}' \
             '{"myorder": "sorted", "inputlist": ["hostA", "hostB", "hostC", "hostD"]}'  \
             '{"myorder": "reverse_sorted", "inputlist": ["hostD", "hostC", "hostB", "hostA"]}' \
             '{"myorder": "reverse_inventory", "inputlist": ["hostC", "hostD", "hostA", "hostB"]}' \
             '{"myorder": "shuffle", "inputlist": ["hostC", "hostD", "hostA", "hostB"]}'
do
    cleanup
    ansible-playbook order.yml --forks 1 -i inventory -e "$EXTRA" "$@"
done
cleanup
