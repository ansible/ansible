#!/usr/bin/env bash

set -eux
ansible-playbook test.yml -i inventory "$@"

for ptype in cache inventory lookup vars
do
	# each plugin type adds 1 from collection
	pre=$(ansible-doc -l -t ${ptype}|wc -l)
	post=$(ansible-doc -l -t ${ptype} --playbook-dir ./|wc -l)
	[[ $pre == $(( $post - 1 )) ]]

	# ensure we ONLY list from the collection
	justcol=$(ansible-doc -l -t ${ptype} --playbook-dir ./ testns.testcol|wc -l)
	[[ $justcol == 1 ]]

	# ensure we get 0 plugins when restricting to collection, but not supplying it
	justcol=$(ansible-doc -l -t ${ptype} testns.testcol|wc -l)
	[[ $justcol == 0 ]]

	# ensure we get 1 plugins when restricting namespace
	justcol=$(ansible-doc -l -t ${ptype} --playbook-dir ./ testns|wc -l)
	[[ $justcol == 1 ]]
done
