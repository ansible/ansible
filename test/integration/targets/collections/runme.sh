#!/usr/bin/env bash

set -eux

export ANSIBLE_COLLECTIONS_PATH=$PWD/collection_root_user:$PWD/collection_root_sys
export ANSIBLE_GATHERING=explicit
export ANSIBLE_HOST_PATTERN_MISMATCH=error
export NO_COLOR=1
unset ANSIBLE_COLLECTIONS_ON_ANSIBLE_VERSION_MISMATCH

# ensure we can call collection module
ansible localhost -m testns.testcoll.testmodule

# ensure we can call collection module with ansible_collections in path
ANSIBLE_COLLECTIONS_PATH=$PWD/collection_root_sys/ansible_collections ansible localhost -m testns.testcoll.testmodule


echo "--- validating callbacks"
# validate FQ callbacks in ansible-playbook
ANSIBLE_CALLBACKS_ENABLED=testns.testcoll.usercallback ansible-playbook noop.yml | grep "usercallback says ok"
# use adhoc for the rest of these tests, must force it to load other callbacks
export ANSIBLE_LOAD_CALLBACK_PLUGINS=1
# validate redirected callback
ANSIBLE_CALLBACKS_ENABLED=formerly_core_callback ansible localhost -m debug 2>&1 | grep -- "usercallback says ok"
## validate missing redirected callback
ANSIBLE_CALLBACKS_ENABLED=formerly_core_missing_callback ansible localhost -m debug 2>&1 | grep -- "Skipping callback plugin 'formerly_core_missing_callback'"
## validate redirected + removed callback (fatal)
ANSIBLE_CALLBACKS_ENABLED=formerly_core_removed_callback ansible localhost -m debug 2>&1 | grep -- "testns.testcoll.removedcallback has been removed"
# validate avoiding duplicate loading of callback, even if using diff names
[ "$(ANSIBLE_CALLBACKS_ENABLED=testns.testcoll.usercallback,formerly_core_callback ansible localhost -m debug 2>&1 | grep -c 'usercallback says ok')" = "1" ]
# ensure non existing callback does not crash ansible
ANSIBLE_CALLBACKS_ENABLED=charlie.gomez.notme ansible localhost -m debug 2>&1 | grep -- "Skipping callback plugin 'charlie.gomez.notme'"

unset ANSIBLE_LOAD_CALLBACK_PLUGINS
# adhoc normally shouldn't load non-default plugins- let's be sure
output=$(ANSIBLE_CALLBACKS_ENABLED=testns.testcoll.usercallback ansible localhost -m debug)
if [[ "${output}" =~ "usercallback says ok" ]]; then echo fail; exit 1; fi

echo "--- validating docs"
# test documentation
ansible-doc testns.testcoll.testmodule -vvv | grep -- "- normal_doc_frag"
# same with symlink
ln -s "${PWD}/testcoll2" ./collection_root_sys/ansible_collections/testns/testcoll2
ansible-doc testns.testcoll2.testmodule2 -vvv | grep "Test module"
# now test we can list with symlink
ansible-doc -l -vvv| grep "testns.testcoll2.testmodule2"

echo "testing bad doc_fragments (expected ERROR message follows)"
# test documentation failure
ansible-doc testns.testcoll.testmodule_bad_docfrags -vvv 2>&1 | grep -- "unknown doc_fragment"

echo "--- validating default collection"
# test adhoc default collection resolution (use unqualified collection module with playbook dir under its collection)

echo "testing adhoc default collection support with explicit playbook dir"
ANSIBLE_PLAYBOOK_DIR=./collection_root_user/ansible_collections/testns/testcoll ansible localhost -m testmodule

# we need multiple plays, and conditional import_playbook is noisy and causes problems, so choose here which one to use...
if [[ ${INVENTORY_PATH} == *.winrm ]]; then
  export TEST_PLAYBOOK=windows.yml
else
  export TEST_PLAYBOOK=posix.yml

  echo "testing default collection support"
  ansible-playbook -i "${INVENTORY_PATH}" collection_root_user/ansible_collections/testns/testcoll/playbooks/default_collection_playbook.yml "$@"
fi

# test redirects and warnings for filter redirects
echo "testing redirect and deprecation display"
ANSIBLE_DEPRECATION_WARNINGS=yes ansible localhost -m debug -a msg='{{ "data" | testns.testredirect.multi_redirect_filter }}' -vvvvv 2>&1 | tee out.txt
cat out.txt

test "$(grep out.txt -ce 'deprecation1' -ce 'deprecation2' -ce 'deprecation3')" == 3
grep out.txt -e 'redirecting (type: filter) testns.testredirect.multi_redirect_filter to testns.testredirect.redirect_filter1'
grep out.txt -e 'Filter "testns.testredirect.multi_redirect_filter"'
grep out.txt -e 'redirecting (type: filter) testns.testredirect.redirect_filter1 to testns.testredirect.redirect_filter2'
grep out.txt -e 'Filter "testns.testredirect.redirect_filter1"'
grep out.txt -e 'redirecting (type: filter) testns.testredirect.redirect_filter2 to testns.testcoll.testfilter'
grep out.txt -e 'Filter "testns.testredirect.redirect_filter2"'

echo "--- validating collections support in playbooks/roles"
# run test playbooks
ansible-playbook -i "${INVENTORY_PATH}" -v "${TEST_PLAYBOOK}" "$@"

if [[ ${INVENTORY_PATH} != *.winrm ]]; then
	ansible-playbook -i "${INVENTORY_PATH}" -v invocation_tests.yml "$@"
fi

echo "--- validating bypass_host_loop with collection search"
ansible-playbook -i host1,host2, -v test_bypass_host_loop.yml "$@"

echo "--- validating inventory"
# test collection inventories
ansible-playbook inventory_test.yml -i a.statichost.yml -i redirected.statichost.yml "$@"

if [[ ${INVENTORY_PATH} != *.winrm ]]; then
	# base invocation tests
	ansible-playbook -i "${INVENTORY_PATH}" -v invocation_tests.yml "$@"

	# run playbook from collection, test default again, but with FQCN
	ansible-playbook -i "${INVENTORY_PATH}" testns.testcoll.default_collection_playbook.yml "$@"

	# run playbook from collection, test default again, but with FQCN and no extension
	ansible-playbook -i "${INVENTORY_PATH}" testns.testcoll.default_collection_playbook "$@"

	# run playbook that imports from collection
	ansible-playbook -i "${INVENTORY_PATH}" import_collection_pb.yml "$@"
fi

# test collection inventories
ansible-playbook inventory_test.yml -i a.statichost.yml -i redirected.statichost.yml "$@"

# test plugin loader redirect_list
ansible-playbook test_redirect_list.yml -v "$@"

# test ansiballz cache dupe
ansible-playbook ansiballz_dupe/test_ansiballz_cache_dupe_shortname.yml -v "$@"

# test adjacent with --playbook-dir
export ANSIBLE_COLLECTIONS_PATH=''
ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED=1 ansible-inventory --list --export --playbook-dir=. -v "$@"

# use an inventory source with caching enabled
ansible-playbook -i a.statichost.yml -i ./cache.statichost.yml -v check_populated_inventory.yml

# Check that the inventory source with caching enabled was stored
if [[ "$(find ./inventory_cache -type f ! -path "./inventory_cache/.keep" | wc -l)" -ne "1" ]]; then
    echo "Failed to find the expected single cache"
    exit 1
fi

CACHEFILE="$(find ./inventory_cache -type f ! -path './inventory_cache/.keep')"

if [[ $CACHEFILE != ./inventory_cache/prefix_* ]]; then
    echo "Unexpected cache file"
    exit 1
fi

# Check the cache for the expected hosts

if [[ "$(grep -wc "cache_host_a" "$CACHEFILE")" -ne "1" ]]; then
    echo "Failed to cache host as expected"
    exit 1
fi

if [[ "$(grep -wc "dynamic_host_a" "$CACHEFILE")" -ne "0" ]]; then
    echo "Cached an incorrect source"
    exit 1
fi

./vars_plugin_tests.sh

./test_task_resolved_plugin.sh

# Test tombstoned module/action plugins include the location of the fatal task
cat <<EOF > test_dead_ping_error.yml
- hosts: localhost
  gather_facts: no
  tasks:
  - dead_ping:
EOF
ansible-playbook test_dead_ping_error.yml 2>&1 >/dev/null | grep -e 'line 4, column 5'
