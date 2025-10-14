#!/usr/bin/env bash

# always set logical error behaviors, enable execution tracing later if sufficient verbosity requested
set -eu

verbosity=0

# default to silent output for naked grep; -vvv+ will adjust this
GREP_OPTS=(-q)

# shell tracing output is very large from this script; only enable if >= -vvv was passed
while getopts :v opt
do  case "$opt" in
      v) ((verbosity+=1)) ;;
      *) ;;
    esac
done

if (( verbosity >= 3 ));
then
  set -x
  GREP_OPTS=()
fi

echo "running playbook-backed docs tests"
ansible-playbook test.yml -i inventory "$@"

# test keyword docs
ansible-doc -t keyword -l | grep "${GREP_OPTS[@]}" 'vars_prompt: list of variables to prompt for.'
ansible-doc -t keyword vars_prompt | grep "${GREP_OPTS[@]}" 'description: list of variables to prompt for.'
ansible-doc -t keyword asldkfjaslidfhals 2>&1 | grep "${GREP_OPTS[@]}" 'Skipping invalid keyword'

echo "Check if deprecation collection name is printed"
ansible-doc --playbook-dir ./ testns.testcol.randommodule 2>&1 | grep "${GREP_OPTS[@]}" "Will be removed in: testns.testcol"

# collections testing
(
unset ANSIBLE_PLAYBOOK_DIR
export ANSIBLE_NOCOLOR=1

cd "$(dirname "$0")"


echo "test fakemodule docs from collection"
# we use sed to strip the module path from the first line
current_out="$(ansible-doc --playbook-dir ./ testns.testcol.fakemodule | sed '1 s/\(^> MODULE testns\.testcol\.fakemodule\).*(.*)$/\1/')"
expected_out="$(sed '1 s/\(^> MODULE testns\.testcol\.fakemodule\).*(.*)$/\1/' fakemodule.output)"
test "$current_out" == "$expected_out"

echo "test randommodule docs from collection"
# we use sed to strip the plugin path from the first line, and fix-urls.py to unbreak and replace URLs from stable-X branches
current_out="$(ansible-doc --playbook-dir ./ testns.testcol.randommodule | sed '1 s/\(^> MODULE testns\.testcol\.randommodule\).*(.*)$/\1/' | python fix-urls.py)"
expected_out="$(sed '1 s/\(^> MODULE testns\.testcol\.randommodule\).*(.*)$/\1/' randommodule-text.output)"
test "$current_out" == "$expected_out"

echo "test yolo filter docs from collection"
# we use sed to strip the plugin path from the first line, and fix-urls.py to unbreak and replace URLs from stable-X branches
current_out="$(ansible-doc --playbook-dir ./ testns.testcol.yolo --type test | sed '1 s/\(^> TEST testns\.testcol\.yolo\).*(.*)$/\1/' | python fix-urls.py)"
expected_out="$(sed '1 s/\(^> TEST testns\.testcol\.yolo\).*(.*)$/\1/' yolo-text.output)"
test "$current_out" == "$expected_out"

# ensure we do work with valid collection name for list
ansible-doc --list testns.testcol --playbook-dir ./ 2>&1 | grep -v "Invalid collection name"

echo "ensure we do work with valid collection name for list"
ansible-doc --list testns.testcol --playbook-dir ./ 2>&1 | grep "${GREP_OPTS[@]}" -v "Invalid collection name"

echo "ensure we dont break on invalid collection name for list"
ansible-doc --list testns.testcol.fakemodule  --playbook-dir ./ 2>&1 | grep "${GREP_OPTS[@]}" "Invalid collection name"

echo "filter list with more than one collection (1/2)"
output=$(ansible-doc --list testns.testcol3 testns.testcol4 --playbook-dir ./ 2>&1 | wc -l)
test "$output" -eq 2

echo "filter list with more than one collection (2/2)"
output=$(ansible-doc --list testns.testcol testns.testcol4 --playbook-dir ./ 2>&1 | wc -l)
test "$output" -eq 5

echo "testing ansible-doc output for various plugin types"
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
	echo "testing collection-filtered list for plugin ${ptype}"
	justcol=$(ansible-doc -l -t ${ptype} --playbook-dir ./ testns.testcol|wc -l)
	test "$justcol" -eq "$expected"

	echo "validate collection plugin name display for plugin ${ptype}"
	list_result=$(ansible-doc -l -t ${ptype} --playbook-dir ./ testns.testcol)
	metadata_result=$(ansible-doc --metadata-dump --no-fail-on-errors -t ${ptype} --playbook-dir ./ testns.testcol)
	for name in "${expected_names[@]}"; do
		echo "${list_result}" | grep "${GREP_OPTS[@]}" "testns.testcol.${name}"
		echo "${metadata_result}" | grep "${GREP_OPTS[@]}" "testns.testcol.${name}"
	done

	# ensure we get error if passing invalid collection, much less any plugins
	ansible-doc -l -t ${ptype} bogus.boguscoll  2>&1 | grep "${GREP_OPTS[@]}" "unable to locate collection"

	# TODO: do we want per namespace?
	# ensure we get 1 plugins when restricting namespace
	#justcol=$(ansible-doc -l -t ${ptype} --playbook-dir ./ testns|wc -l)
	#test "$justcol" -eq 1
done

#### test role functionality

echo "testing role text output"
# we use sed to strip the role path from the first line
current_role_out="$(ansible-doc -t role -r ./roles test_role1 | sed '1 s/\(^> ROLE: \*test_role1\*\).*(.*)$/\1/' | python fix-urls.py)"
expected_role_out="$(sed '1 s/\(^> ROLE: \*test_role1\*\).*(.*)$/\1/' fakerole.output)"
test "$current_role_out" == "$expected_role_out"

echo "testing multiple role entrypoints"
# Two collection roles are defined, but only 1 has a role arg spec with 2 entry points
output=$(ansible-doc -t role -l --playbook-dir . testns.testcol | wc -l)
test "$output" -eq 4

echo "test listing roles with multiple collection filters"
# Two collection roles are defined, but only 1 has a role arg spec with 2 entry points
output=$(ansible-doc -t role -l --playbook-dir . testns.testcol2 testns.testcol | wc -l)
test "$output" -eq 4

echo "testing standalone roles"
# Include normal roles (no collection filter)
output=$(ansible-doc -t role -l --playbook-dir . | wc -l)
test "$output" -eq 11

echo "testing role precedence"
# Test that a role in the playbook dir with the same name as a role in the
# 'roles' subdir of the playbook dir does not appear (lower precedence).
output=$(ansible-doc -t role -l --playbook-dir . | grep -c "test_role1 from roles subdir")
test "$output" -eq 1
output=$(ansible-doc -t role -l --playbook-dir . | grep -c "test_role1 from playbook dir" || true)
test "$output" -eq 0

echo "testing role entrypoint filter"
current_role_out="$(ansible-doc -t role --playbook-dir . testns.testcol.testrole -e alternate| sed '1 s/\(^> ROLE: \*testns\.testcol\.testrole\*\).*(.*)$/\1/')"
expected_role_out="$(sed '1 s/\(^> ROLE: \*testns\.testcol\.testrole\*\).*(.*)$/\1/' fakecollrole.output)"
test "$current_role_out" == "$expected_role_out"

)

#### test add_collection_to_versions_and_dates()

echo "testing json output"
current_out="$(ansible-doc --json --playbook-dir ./ testns.testcol.randommodule | sed 's/ *$//' | sed 's/ *"filename": "[^"]*",$//')"
expected_out="$(sed 's/ *"filename": "[^"]*",$//' randommodule.output)"
test "$current_out" == "$expected_out"

echo "testing json output 2"
current_out="$(ansible-doc --json --playbook-dir ./ testns.testcol.yolo --type test | sed 's/ *$//' | sed 's/ *"filename": "[^"]*",$//')"
expected_out="$(sed 's/ *"filename": "[^"]*",$//' yolo.output)"
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

echo "testing metadata dump"
# just ensure it runs
ANSIBLE_LIBRARY='./nolibrary' ansible-doc --metadata-dump --playbook-dir /dev/null 1>/dev/null 2>&1

echo "test metadata dump on broken role metadata"
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
ANSIBLE_LIBRARY='./nolibrary' ansible-doc --metadata-dump --no-fail-on-errors --playbook-dir broken-docs testns.testcol 1>/dev/null 2>&1

# ensure that --metadata-dump does fail when --no-fail-on-errors is not supplied
output=$(ANSIBLE_LIBRARY='./nolibrary' ansible-doc --metadata-dump --playbook-dir broken-docs testns.testcol 2>&1 | grep -c 'ERROR' || true)
test "${output}" -eq 1

# ensure --metadata-dump does not crash if the ansible_collections is nested (https://github.com/ansible/ansible/issues/84909)
testdir="$(pwd)"
pbdir="collections/ansible_collections/testns/testcol/playbooks"
cd "$pbdir"
ANSIBLE_COLLECTIONS_PATH="$testdir/$pbdir/collections" ansible-doc -vvv --metadata-dump --no-fail-on-errors
cd "$testdir"

echo "test doc list on broken role metadata"
# ensure that role doc does not fail when --no-fail-on-errors is supplied
ANSIBLE_LIBRARY='./nolibrary' ansible-doc --no-fail-on-errors --playbook-dir broken-docs testns.testcol.testrole -t role 1>/dev/null 2>&1

# ensure that role doc does fail when --no-fail-on-errors is not supplied
output=$(ANSIBLE_LIBRARY='./nolibrary' ansible-doc --playbook-dir broken-docs testns.testcol.testrole -t role 2>&1 | grep -c 'ERROR' || true)
test "${output}" -eq 1

echo "testing legacy plugin listing"
[ "$(ansible-doc -M ./library -l ansible.legacy |wc -l)"  -gt "0" ]

echo "testing legacy plugin list via --playbook-dir"
[ "$(ansible-doc -l ansible.legacy --playbook-dir ./|wc -l)" -gt "0" ]

echo "testing undocumented plugin output"
[ "$(ansible-doc -M ./library -l ansible.legacy |grep -c UNDOCUMENTED)" == "6" ]

echo "testing filtering does not include any 'test_' modules"
[ "$(ansible-doc -M ./library -l ansible.builtin |grep -c test_)" == 0 ]
[ "$(ansible-doc --playbook-dir ./  -l ansible.builtin |grep -c test_)" == 0 ]

echo "testing filtering still shows modules"
count=$(ANSIBLE_LIBRARY='./nolibrary' ansible-doc -l ansible.builtin |wc -l)
[ "${count}" -gt "0" ]
[ "$(ansible-doc -M ./library -l ansible.builtin |wc -l)" == "${count}" ]
[ "$(ansible-doc --playbook-dir ./ -l ansible.builtin |wc -l)" == "${count}" ]


echo "testing sidecar docs for jinja plugins"
[ "$(ansible-doc -t test --playbook-dir ./ testns.testcol.yolo| wc -l)" -gt "0" ]
[ "$(ansible-doc -t filter --playbook-dir ./ donothing| wc -l)" -gt "0" ]
[ "$(ansible-doc -t filter --playbook-dir ./ ansible.legacy.donothing| wc -l)" -gt "0" ]
[ "$(ansible-doc -t filter --playbook-dir ./ testns.testcol.filter_subdir.nested| wc -l)" -gt "0" ]

echo "testing no docs and no sidecar"
ansible-doc -t filter --playbook-dir ./ nodocs 2>&1| grep "${GREP_OPTS[@]}" -c 'missing documentation' || true

echo "testing sidecar docs for module"
[ "$(ansible-doc -M ./library test_win_module| wc -l)" -gt "0" ]
[ "$(ansible-doc --playbook-dir ./ test_win_module| wc -l)" -gt "0" ]

echo "testing duplicate DOCUMENTATION"
[ "$(ansible-doc --playbook-dir ./ double_doc| wc -l)" -gt "0" ]

echo "testing don't break on module dir"
ansible-doc --list --module-path ./modules > /dev/null

echo "testing dedupe by fqcn and not base name"
[ "$(ansible-doc -l -t filter --playbook-dir ./ |grep -c 'b64decode')" -eq "3" ]

echo "testing no duplicates for plugins that only exist in ansible.builtin when listing ansible.legacy plugins"
[ "$(ansible-doc -l -t filter --playbook-dir ./ |grep -c 'b64encode')" -eq "1" ]

echo "testing with playbook dir, legacy should override"
ansible-doc -t filter split --playbook-dir ./ -v|grep "${GREP_OPTS[@]}" histerical

pyc_src="$(pwd)/filter_plugins/other.py"
pyc_1="$(pwd)/filter_plugins/split.pyc"
pyc_2="$(pwd)/library/notaplugin.pyc"
trap 'rm -rf "$pyc_1" "$pyc_2"' EXIT

echo "testing pyc files are not used as adjacent documentation"
python -c "import py_compile; py_compile.compile('$pyc_src', cfile='$pyc_1')"
ansible-doc -t filter split --playbook-dir ./ -v|grep "${GREP_OPTS[@]}" histerical

echo "testing pyc files are not listed as plugins"
python -c "import py_compile; py_compile.compile('$pyc_src', cfile='$pyc_2')"
test "$(ansible-doc -l -t module --playbook-dir ./ 2>&1 1>/dev/null |grep -c "notaplugin")" == 0

echo "testing without playbook dir, builtin should return"
ansible-doc -t filter split -v 2>&1 |grep "${GREP_OPTS[@]}" -v histerical

echo "test 'sidecar' for no extension module  with .py doc"
[ "$(ansible-doc -M ./library -l ansible.legacy |grep -v 'UNDOCUMENTED' |grep -c bogus_facts)" == "1" ]

echo "test 'sidecar' for no extension module  with .yml doc"
[ "$(ansible-doc -M ./library -l ansible.legacy |grep -v 'UNDOCUMENTED' |grep -c facts_one)" == "1" ]

echo "test j2 plugins get jinja2 instead of path"
ansible-doc -t filter map 2>&1 |grep "${GREP_OPTS[@]}" '(Jinja2)'

echo "test missing description in test_role4 argument spec"
ansible-doc -t role -r ./roles test_role4 2>&1 >/dev/null | grep -q 'Error extracting role docs from '\''test_role4'\'': All (sub-)options and return values must have a '\''description'\'' field'
