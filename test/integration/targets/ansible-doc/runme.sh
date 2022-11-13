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

# we use sed to strip the module path from the first line
current_out="$(ansible-doc --playbook-dir ./ testns.testcol.randommodule | sed '1 s/\(^> TESTNS\.TESTCOL\.RANDOMMODULE\).*(.*)$/\1/')"
expected_out="$(sed '1 s/\(^> TESTNS\.TESTCOL\.RANDOMMODULE\).*(.*)$/\1/' randommodule-text.output)"
test "$current_out" == "$expected_out"

# ensure we do work with valid collection name for list
ansible-doc --list testns.testcol --playbook-dir ./ 2>&1 | grep -v "Invalid collection name"

# ensure we dont break on invalid collection name for list
ansible-doc --list testns.testcol.fakemodule  --playbook-dir ./ 2>&1 | grep "Invalid collection name"

# test that directly showing docs for private plugins in collections works
ansible-doc testns.testcol.hidden -t filter --playbook-dir . | grep "TESTNS.TESTCOL.HIDDEN"
ansible-doc testns.testcol.hidden -t module --playbook-dir . | grep "TESTNS.TESTCOL.HIDDEN"

# test listing diff plugin types from collection
for ptype in cache inventory lookup vars filter module
do
	# each plugin type adds 1 from collection
	# FIXME pre=$(ansible-doc -l -t ${ptype}|wc -l)
	# FIXME post=$(ansible-doc -l -t ${ptype} --playbook-dir ./|wc -l)
	# FIXME test "$pre" -eq $((post - 1))
	if [ "${ptype}" == "filter" ]; then
		expected=5
		expected_names=("b64decode" "filter_subdir.nested" "filter_subdir.noop" "noop" "ultimatequestion")
	elif [ "${ptype}" == "module" ]; then
		expected=4
		expected_names=("fakemodule" "notrealmodule" "randommodule" "database.database_type.subdir_module")
	else
		expected=1
                if [ "${ptype}" == "cache" ]; then expected_names=("notjsonfile");
                elif [ "${ptype}" == "inventory" ]; then expected_names=("statichost");
                elif [ "${ptype}" == "lookup" ]; then expected_names=("noop");
                elif [ "${ptype}" == "vars" ]; then expected_names=("noop_vars_plugin"); fi
	fi
	# ensure we ONLY list from the collection
	justcol=$(ansible-doc -l -t ${ptype} --playbook-dir ./ testns.testcol|wc -l)
	test "$justcol" -eq "$expected"

	# ensure the right names are displayed
	list_result=$(ansible-doc -l -t ${ptype} --playbook-dir ./ testns.testcol)
	metadata_result=$(ansible-doc --metadata-dump --no-fail-on-errors -t ${ptype} --playbook-dir ./ testns.testcol)
	for name in "${expected_names[@]}"; do
		echo "${list_result}" | grep "testns.testcol.${name}"
		echo "${metadata_result}" | grep "testns.testcol.${name}"
	done

	# ensure we get error if passinginvalid collection, much less any plugins
	ansible-doc -l -t ${ptype} testns.testcol  2>&1 | grep "unable to locate collection"

	# TODO: do we want per namespace?
	# ensure we get 1 plugins when restricting namespace
	#justcol=$(ansible-doc -l -t ${ptype} --playbook-dir ./ testns|wc -l)
	#test "$justcol" -eq 1
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

# just ensure it runs
ANSIBLE_LIBRARY='./nolibrary' ansible-doc --metadata-dump --playbook-dir /dev/null >/dev/null

# create broken role argument spec
mkdir -p broken-docs/collections/ansible_collections/testns/testcol/roles/testrole/meta
cat <<EOF > broken-docs/collections/ansible_collections/testns/testcol/roles/testrole/meta/main.yml
---
dependencies:
galaxy_info:

argument_specs:
    main:
        short_description: testns.testcol.testrole short description for main entry point
        description:
            - Longer description for testns.testcol.testrole main entry point.
        author: Ansible Core (@ansible)
        options:
            opt1:
                description: opt1 description
                    broken:
                type: "str"
                required: true
EOF

# ensure that --metadata-dump does not fail when --no-fail-on-errors is supplied
ANSIBLE_LIBRARY='./nolibrary' ansible-doc --metadata-dump --no-fail-on-errors --playbook-dir broken-docs testns.testcol >/dev/null

# ensure that --metadata-dump does fail when --no-fail-on-errors is not supplied
output=$(ANSIBLE_LIBRARY='./nolibrary' ansible-doc --metadata-dump --playbook-dir broken-docs testns.testcol 2>&1 | grep -c 'ERROR!' || true)
test "${output}" -eq 1

# ensure we list the 'legacy plugins'
[ "$(ansible-doc -M ./library -l ansible.legacy |wc -l)"  -gt "0" ]

# playbook dir should work the same
[ "$(ansible-doc -l ansible.legacy --playbook-dir ./|wc -l)" -gt "0" ]

# see that we show undocumented when missing docs
[ "$(ansible-doc -M ./library -l ansible.legacy |grep -c UNDOCUMENTED)" == "6" ]

# ensure filtering works and does not include any 'test_' modules
[ "$(ansible-doc -M ./library -l ansible.builtin |grep -c test_)" == 0 ]
[ "$(ansible-doc --playbook-dir ./  -l ansible.builtin |grep -c test_)" == 0 ]

# ensure filtering still shows modules
count=$(ANSIBLE_LIBRARY='./nolibrary' ansible-doc -l ansible.builtin |wc -l)
[ "${count}" -gt "0" ]
[ "$(ansible-doc -M ./library -l ansible.builtin |wc -l)" == "${count}" ]
[ "$(ansible-doc --playbook-dir ./ -l ansible.builtin |wc -l)" == "${count}" ]


# produce 'sidecar' docs for test
[ "$(ansible-doc -t test --playbook-dir ./ testns.testcol.yolo| wc -l)" -gt "0" ]
[ "$(ansible-doc -t filter --playbook-dir ./ donothing| wc -l)" -gt "0" ]
[ "$(ansible-doc -t filter --playbook-dir ./ ansible.legacy.donothing| wc -l)" -gt "0" ]

# no docs and no sidecar
ansible-doc -t filter --playbook-dir ./ nodocs 2>&1| grep -c 'missing documentation' || true

# produce 'sidecar' docs for module
[ "$(ansible-doc -M ./library test_win_module| wc -l)" -gt "0" ]
[ "$(ansible-doc --playbook-dir ./ test_win_module| wc -l)" -gt "0" ]

# test 'double DOCUMENTATION' use
[ "$(ansible-doc --playbook-dir ./ double_doc| wc -l)" -gt "0" ]

# don't break on module dir
ansible-doc --list --module-path ./modules > /dev/null

# ensure we dedupe by fqcn and not base name
[ "$(ansible-doc -l -t filter --playbook-dir ./ |grep -c 'b64decode')" -eq "3" ]

# ensure we don't show duplicates for plugins that only exist in ansible.builtin when listing ansible.legacy plugins
[ "$(ansible-doc -l -t filter --playbook-dir ./ |grep -c 'b64encode')" -eq "1" ]

# with playbook dir, legacy should override
ansible-doc -t filter split --playbook-dir ./ |grep histerical

pyc_src="$(pwd)/filter_plugins/other.py"
pyc_1="$(pwd)/filter_plugins/split.pyc"
pyc_2="$(pwd)/library/notaplugin.pyc"
trap 'rm -rf "$pyc_1" "$pyc_2"' EXIT

# test pyc files are not used as adjacent documentation
python -c "import py_compile; py_compile.compile('$pyc_src', cfile='$pyc_1')"
ansible-doc -t filter split --playbook-dir ./ |grep histerical

# test pyc files are not listed as plugins
python -c "import py_compile; py_compile.compile('$pyc_src', cfile='$pyc_2')"
test "$(ansible-doc -l -t module --playbook-dir ./ 2>&1 1>/dev/null |grep -c "notaplugin")" == 0

# without playbook dir, builtin should return
ansible-doc -t filter split |grep -v histerical
