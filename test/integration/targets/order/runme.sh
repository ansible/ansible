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

for EXTRA in '{"inputlist": ["host-dc1-02", "host-dc2-01", "host-dc1-01", "host-dc2-02"]}' \
             '{"myorder": "inventory", "inputlist": ["host-dc1-02", "host-dc2-01", "host-dc1-01", "host-dc2-02"]}' \
             '{"myorder": "sorted", "inputlist": ["host-dc1-01", "host-dc1-02", "host-dc2-01", "host-dc2-02"]}'  \
             '{"myorder": "reverse_sorted", "inputlist": ["host-dc2-02", "host-dc2-01", "host-dc1-02", "host-dc1-01"]}' \
             '{"myorder": "backward_sorted", "inputlist": ["host-dc1-01", "host-dc2-01", "host-dc1-02", "host-dc2-02"]}'  \
             '{"myorder": "backward_reverse_sorted", "inputlist": ["host-dc2-02", "host-dc1-02", "host-dc2-01", "host-dc1-01"]}' \
             '{"myorder": "reverse_inventory", "inputlist": ["host-dc2-02", "host-dc1-01", "host-dc2-01", "host-dc1-02"]}' \
             '{"myorder": "shuffle", "inputlist": ["host-dc2-02", "host-dc1-01", "host-dc2-01", "host-dc1-02"]}'
do
    cleanup
    ansible-playbook order.yml --forks 1 -i inventory -e "$EXTRA" "$@"
done
cleanup
