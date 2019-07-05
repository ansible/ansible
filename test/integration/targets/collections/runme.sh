#!/usr/bin/env bash

set -eux

export ANSIBLE_COLLECTIONS_PATHS=$PWD/collection_root_user:$PWD/collection_root_sys
export ANSIBLE_GATHERING=explicit
export ANSIBLE_GATHER_SUBSET=minimal
export ANSIBLE_HOST_PATTERN_MISMATCH=error

# FIXME: just use INVENTORY_PATH as-is once ansible-test sets the right dir
ipath=../../$(basename "${INVENTORY_PATH}")
export INVENTORY_PATH="$ipath"

# temporary hack to keep this test from running on Python 2.6 in CI
if ansible-playbook pythoncheck.yml | grep UNSUPPORTEDPYTHON; then
  echo skipping test for unsupported Python version...
  exit 0
fi

# test callback
ANSIBLE_CALLBACK_WHITELIST=testns.testcoll.usercallback ansible localhost -m ping | grep "usercallback says ok"

# test documentation
ansible-doc testns.testcoll.testmodule -vvv | grep -- "- normal_doc_frag"

# we need multiple plays, and conditional import_playbook is noisy and causes problems, so choose here which one to use...
if [[ ${INVENTORY_PATH} == *.winrm ]]; then
  export TEST_PLAYBOOK=windows.yml
else
  export TEST_PLAYBOOK=posix.yml
fi

# run test playbook
ansible-playbook -i "${INVENTORY_PATH}"  -i ./a.statichost.yml -v "${TEST_PLAYBOOK}"

# test adjacent with --playbook-dir
export ANSIBLE_COLLECTIONS_PATHS=''
ANSIBLE_INVENTORY_ANY_UNPARSED_IS_FAILED=1 ansible-inventory -i a.statichost.yml --list --export --playbook-dir=. -v "$@"
