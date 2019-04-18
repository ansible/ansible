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

# Run test if dependencies are installed
failed_dep_1=$(ansible localhost -m pip -a "name=redis>=2.4.5 state=present" "$@" | tee out.txt | grep -c 'FAILED!' || true)
cat out.txt

installed_redis=$(ansible localhost -m package -a "name=redis-server state=present" --become "$@" | tee out.txt | grep -c '"changed": true' || true)
failed_dep_2=$(grep out.txt -ce 'FAILED!' || true)
cat out.txt

started_redis=$(ansible localhost -m service -a "name=redis-server state=started" --become "$@" | tee out.txt | grep -c '"changed": true' || true)
failed_dep_3=$(grep out.txt -ce 'FAILED!' || true)
cat out.txt

CLEANUP_REDIS () { if [ "${installed_redis}" -eq 1 ] ; then ansible localhost -m package -a "name=redis-server state=absent" --become ; fi }
STOP_REDIS () { if [ "${installed_redis}" -ne 1 ] && [ "${started_redis}" -eq 1 ] ; then ansible localhost -m service -a "name=redis-server state=stopped" --become ; fi }

if [ "${failed_dep_1}" -eq 1 ] || [ "${failed_dep_2}" -eq 1 ] || [ "${failed_dep_3}" -eq 1 ] ; then
    STOP_REDIS
    CLEANUP_REDIS
    exit 0
fi

export ANSIBLE_CACHE_PLUGIN=redis
export ANSIBLE_CACHE_PLUGIN_CONNECTION=localhost:6379:0
export ANSIBLE_CACHE_PLUGINS=./plugins/cache

# Use old redis for fact caching
count=$(ansible-playbook test_fact_gathering.yml -vvv 2>&1 "$@" | tee out.txt | grep -c 'Gathering Facts' || true)
failed_dep_version=$(grep out.txt -ce "'redis' python module (version 2.4.5 or newer) is required" || true)
cat out.txt
if [ "${failed_dep_version}" -eq 1 ] ; then
    STOP_REDIS
    CLEANUP_REDIS
    exit 0
fi
if [ "${count}" -ne 1 ] ; then
    STOP_REDIS
    CLEANUP_REDIS
    exit 1
fi

# Attempt to use old redis for inventory caching; should not work
export ANSIBLE_INVENTORY_CACHE=True
export ANSIBLE_INVENTORY_CACHE_PLUGIN=redis
export ANSIBLE_INVENTORY_ENABLED=test
export ANSIBLE_INVENTORY_PLUGINS=./plugins/inventory

ansible-inventory -i inventory_config --graph 2>&1 "$@" | tee out.txt | grep 'Cache options were provided but may not reconcile correctly unless set via set_options'
res=$?
cat out.txt
if [ "${res}" -eq 1 ] ; then
    STOP_REDIS
    CLEANUP_REDIS
    exit 1
fi

# Use new style redis for fact caching
unset ANSIBLE_CACHE_PLUGINS
count=$(ansible-playbook test_fact_gathering.yml -vvv "$@" | tee out.txt | grep -c 'Gathering Facts' || true)
cat out.txt
if [ "${count}" -ne 1 ] ; then
    STOP_REDIS
    CLEANUP_REDIS
    exit 1
fi

# Use new redis for inventory caching
ansible-inventory -i inventory_config --graph "$@" 2>&1 | tee out.txt | grep 'host2'
res=$?
cat out.txt

STOP_REDIS
CLEANUP_REDIS

exit $res
