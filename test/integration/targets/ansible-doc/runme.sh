#!/usr/bin/env bash

set -eux
ansible-playbook test.yml -i inventory "$@"

# test keyword docs
ansible-doc -t keyword -l | grep 'vars_prompt: list of variables to prompt for.'
ansible-doc -t keyword vars_prompt | grep 'description: list of variables to prompt for.'
ansible-doc -t keyword asldkfjaslidfhals 2>&1 | grep 'Skipping Invalid keyword'

# collections testing
(
unset ANSIBLE_PLAYBOOK_DIR
cd "$(dirname "$0")"

# test module docs from collection
# we use sed to strip the module path from the first line
current_out="$(ansible-doc --playbook-dir ./ testns.testcol.fakemodule | sed '1 s/\(^> TESTNS\.TESTCOL\.FAKEMODULE\).*(.*)$/\1/')"
expected_out="$(sed '1 s/\(^> TESTNS\.TESTCOL\.FAKEMODULE\).*(.*)$/\1/' fakemodule.output)"
test "$current_out" == "$expected_out"

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

#### test role functionality

# Two collection roles are defined, but only 1 has a role arg spec with 2 entry points
output=$(ansible-doc -t role -l --playbook-dir . testns.testcol | wc -l)
test "$output" -eq 2

# Include normal roles
output=$(ansible-doc -t role -l --playbook-dir . --roles-path ./roles | wc -l)
test "$output" -eq 3
)
