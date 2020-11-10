#!/usr/bin/env bash

set -eux
ansible-playbook test.yml -i inventory "$@"

(
unset ANSIBLE_PLAYBOOK_DIR
cd "$(dirname "$0")"

# test module docs from collection
current_out="$(ansible-doc --playbook-dir ./ testns.testcol.fakemodule)"
expected_out="$(cat fakemodule.output)"
test "$current_out" == "$expected_out"

# ensure we do work with valid collection name for list
ansible-doc --list testns.testcol --playbook-dir ./ 2>&1 | grep -v "Invalid collection pattern"

# ensure we dont break on invalid collection name for list
ansible-doc --list testns.testcol.fakemodule  --playbook-dir ./ 2>&1 | grep "Invalid collection pattern"


# test listing diff plugin types from collection
for ptype in cache inventory lookup vars
do
	# each plugin type adds 1 from collection
	# FIXME pre=$(ansible-doc -l -t ${ptype}|wc -l)
	# FIXME post=$(ansible-doc -l -t ${ptype} --playbook-dir ./|wc -l)
	# FIXME test "$pre" -eq $((post - 1))

	# ensure we ONLY list from the collection
	justcol=$(ansible-doc -l -t ${ptype} --playbook-dir ./ testns.testcol|wc -l)
	test "$justcol" -eq 1

	# ensure we get 0 plugins when restricting to collection, but not supplying it
	justcol=$(ansible-doc -l -t ${ptype} testns.testcol|wc -l)
	test "$justcol" -eq 0

	# ensure we get 1 plugins when restricting namespace
	justcol=$(ansible-doc -l -t ${ptype} --playbook-dir ./ testns|wc -l)
	test "$justcol" -eq 1
done
)
