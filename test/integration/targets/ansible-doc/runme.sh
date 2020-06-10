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

# test module docs from collection
# (The sed expression trims the absolute (machine and run dependent) path so this is reproducible.)
current_out="$(ansible-doc --playbook-dir ./ test_docs_suboptions | sed -E 's/^(> [A-Z_]+ +\()[^)]+library\/([a-z_]+.py)\)$/\1library\/\2\)/')"
expected_out="$(cat test_docs_suboptions.output)"
test "$current_out" == "$expected_out"

# test module with return values
# (The sed expression trims the absolute (machine and run dependent) path so this is reproducible.)
current_out="$(ansible-doc --playbook-dir ./ test_docs_returns | sed -E 's/^(> [A-Z_]+ +\()[^)]+library\/([a-z_]+.py)\)$/\1library\/\2\)/')"
expected_out="$(cat test_docs_returns.output)"
test "$current_out" == "$expected_out"

# test module with broken return values (YAML parsing fails)
set +e
current_err="$(ansible-doc --playbook-dir ./ test_docs_returns_broken 2>&1 > /dev/null)"
RC=$?
set -e
test $RC == 1
[[ "$current_err" =~ .*"ERROR! module test_docs_returns_broken missing documentation (or could not parse documentation)".* ]]

# test listing diff plugin types from collection
for ptype in cache inventory lookup vars
do
	# each plugin type adds 1 from collection
	pre=$(ansible-doc -l -t ${ptype}|wc -l)
	post=$(ansible-doc -l -t ${ptype} --playbook-dir ./|wc -l)
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
