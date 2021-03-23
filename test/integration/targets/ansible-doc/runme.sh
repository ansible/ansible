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

#### test role functionality

# Test role text output
# we use sed to strip the role path from the first line
current_role_out="$(ansible-doc -t role -r ./roles test_role1 | sed '1 s/\(^> TEST_ROLE1\).*(.*)$/\1/')"
expected_role_out="$(sed '1 s/\(^> TEST_ROLE1\).*(.*)$/\1/' fakerole.output)"
test "$current_role_out" == "$expected_role_out"

# Two collection roles are defined, but only 1 has a role arg spec with 2 entry points
output=$(ansible-doc -t role -l --playbook-dir . testns.testcol | wc -l)
test "$output" -eq 2

# Include normal roles (no collection filter)
output=$(ansible-doc -t role -l --playbook-dir . | wc -l)
test "$output" -eq 3

# Test that a role in the playbook dir with the same name as a role in the
# 'roles' subdir of the playbook dir does not appear (lower precedence).
output=$(ansible-doc -t role -l --playbook-dir . | grep -c "test_role1 from roles subdir")
test "$output" -eq 1
output=$(ansible-doc -t role -l --playbook-dir . | grep -c "test_role1 from playbook dir" || true)
test "$output" -eq 0

# Test entry point filter
current_role_out="$(ansible-doc -t role --playbook-dir . testns.testcol.testrole -e alternate| sed '1 s/\(^> TESTNS\.TESTCOL\.TESTROLE\).*(.*)$/\1/')"
expected_role_out="$(sed '1 s/\(^> TESTNS\.TESTCOL\.TESTROLE\).*(.*)$/\1/' fakecollrole.output)"
test "$current_role_out" == "$expected_role_out"

)

#### test add_collection_to_versions_and_dates()

current_out="$(ansible-doc --json --playbook-dir ./ testns.testcol.randommodule | sed 's/ *$//' | sed 's/ *"filename": "[^"]*",$//')"
expected_out="$(sed 's/ *"filename": "[^"]*",$//' randommodule.output)"
test "$current_out" == "$expected_out"

current_out="$(ansible-doc --json --playbook-dir ./ -t cache testns.testcol.notjsonfile | sed 's/ *$//' | sed 's/ *"filename": "[^"]*",$//')"
expected_out="$(sed 's/ *"filename": "[^"]*",$//' notjsonfile.output)"
test "$current_out" == "$expected_out"

current_out="$(ansible-doc --json --playbook-dir ./ -t lookup testns.testcol.noop | sed 's/ *$//' | sed 's/ *"filename": "[^"]*",$//')"
expected_out="$(sed 's/ *"filename": "[^"]*",$//' noop.output)"
test "$current_out" == "$expected_out"

current_out="$(ansible-doc --json --playbook-dir ./ -t vars testns.testcol.noop_vars_plugin | sed 's/ *$//' | sed 's/ *"filename": "[^"]*",$//')"
expected_out="$(sed 's/ *"filename": "[^"]*",$//' noop_vars_plugin.output)"
test "$current_out" == "$expected_out"
