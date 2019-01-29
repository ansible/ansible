#!/usr/bin/env bash

# We don't set -u here, due to pypa/virtualenv#150
set -ex

MYTMPDIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')

trap 'rm -rf "${MYTMPDIR}"' EXIT

# This is needed for the ubuntu1604py3 tests
# Ubuntu patches virtualenv to make the default python2
# but for the python3 tests we need virtualenv to use python3
PYTHON=${ANSIBLE_TEST_PYTHON_INTERPRETER:-python}

virtualenv --system-site-packages --python "${PYTHON}" "${MYTMPDIR}/redis-cache"
source "${MYTMPDIR}/redis-cache/bin/activate"
$PYTHON -m pip install redis

export ANSIBLE_CACHE_PLUGIN=redis
export ANSIBLE_CACHE_PLUGIN_CONNECTION=localhost:6379:0
export ANSIBLE_CACHE_PLUGINS=./plugins/cache

# Use old redis for fact caching
count=$(ansible-playbook test_fact_gathering.yml -vvv "$@" | tee out.txt | grep -c 'Gathering Facts')
cat out.txt
if [ "${count}" -ne 1 ] ; then
    exit 1
fi

# Attempt to use old redis for inventory caching; should not work
export ANSIBLE_INVENTORY_CACHE=True
export ANSIBLE_INVENTORY_CACHE_PLUGIN=redis
export ANSIBLE_INVENTORY_ENABLED=test
export ANSIBLE_INVENTORY_PLUGINS=./plugins/inventory

ansible-inventory --graph 2>&1 | tee out.txt | grep 'Refer to the porting guide if the plugin derives user settings from ansible.constants.'
res=$?
cat out.txt
if [ "${res}" -eq 1 ] ; then
    exit 1
fi

# Use new style redis for fact caching
unset ANSIBLE_CACHE_PLUGINS
count=$(ansible-playbook test_fact_gathering.yml -vvv "$@" | tee out.txt | grep -c 'Gathering Facts')
cat out.txt
if [ "${count}" -ne 1 ] ; then
    exit 1
fi

# Use new redis for inventory caching
ansible-inventory --graph 2>&1 | tee out.txt | grep 'host2'
res=$?
cat out.txt
exit $res
