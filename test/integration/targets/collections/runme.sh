#!/usr/bin/env bash

set -eux

export ANSIBLE_COLLECTIONS_PATHS=$PWD/collection_root_user:$PWD/collection_root_sys
export ANSIBLE_GATHERING=explicit
export ANSIBLE_GATHER_SUBSET=minimal
export ANSIBLE_HOST_PATTERN_MISMATCH=error


# FUTURE: just use INVENTORY_PATH as-is once ansible-test sets the right dir
ipath=../../$(basename "${INVENTORY_PATH}")
export INVENTORY_PATH="$ipath"

# test callback
ANSIBLE_LOAD_CALLBACK_PLUGINS=1 ANSIBLE_CALLBACK_WHITELIST=testns.testcoll.usercallback ansible localhost -m ping | grep "usercallback says ok"

# test documentation
ansible-doc testns.testcoll.testmodule -vvv | grep -- "- normal_doc_frag"

# test adhoc default collection resolution (use unqualified collection module with playbook dir under its collection)
echo "testing adhoc default collection support with explicit playbook dir"
ANSIBLE_PLAYBOOK_DIR=./collection_root_user/ansible_collections/testns/testcoll ansible localhost -m testmodule

echo "testing bad doc_fragments (expected ERROR message follows)"
# test documentation failure
ansible-doc testns.testcoll.testmodule_bad_docfrags -vvv 2>&1 | grep -- "unknown doc_fragment"

# we need multiple plays, and conditional import_playbook is noisy and causes problems, so choose here which one to use...
if [[ ${INVENTORY_PATH} == *.winrm ]]; then
  export TEST_PLAYBOOK=windows.yml
else
  export TEST_PLAYBOOK=posix.yml

  echo "testing default collection support"
  ansible-playbook -i "${INVENTORY_PATH}" collection_root_user/ansible_collections/testns/testcoll/playbooks/default_collection_playbook.yml
fi

# run test playbook
ansible-playbook -i "${INVENTORY_PATH}"  -i ./a.statichost.yml -v "${TEST_PLAYBOOK}" "$@"

# test adjacent with --playbook-dir
export ANSIBLE_COLLECTIONS_PATHS=''
ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED=1 ansible-inventory -i a.statichost.yml --list --export --playbook-dir=. -v "$@"

# ensure non existing callback does not crash ansible
ANSIBLE_CALLBACK_WHITELIST=charlie.gomez.notme ansible -m ping localhost
