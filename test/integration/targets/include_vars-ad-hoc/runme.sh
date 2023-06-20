#!/usr/bin/env bash

set -eux

ansible testhost -i ../../inventory -m include_vars -a 'dir/inc.yml' "$@"
ansible testhost -i ../../inventory -m include_vars -a 'dir=dir' "$@"

ansible-playbook playbook.yml>output.txt
if grep -q '"insidervariable": "config212",' output.txt && \
   grep -q '"insidevar1": "config11",' output.txt && \
   grep -q '"insidevar11-2": "config11-2",' output.txt && \
   grep -q '"insidevar2": "config211",' output.txt && \
   grep -q '"porter": "cable",' output.txt && \
   grep -q '"var1": "sub1var1",' output.txt && \
   grep -q '"var12": "sub1var2",' output.txt && \
   grep -q '"var21": "sub21",' output.txt && \
   grep -q '"variable3": "config3"' output.txt; then
	echo "All lines are present in output.txt"
	rm output.txt
	exit 0
fi
echo "One or more lines are missing from output.txt"
rm output.txt
exit 1
