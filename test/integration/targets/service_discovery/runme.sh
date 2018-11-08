#!/usr/bin/env bash

# We don't set -u here, due to pypa/virtualenv#150
set -ex

MYTMPDIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')

trap 'rm -rf "${MYTMPDIR}"' EXIT

# This is needed for the ubuntu1604py3 tests
# Ubuntu patches virtualenv to make the default python2
# but for the python3 tests we need virtualenv to use python3
PYTHON=${ANSIBLE_TEST_PYTHON_INTERPRETER:-python}

# servicediscovery has been touched in 3 botocore versions, 1.8.8, 1.9.8 1.8.38
# looks like 1.9.8 added custom health check, so I'm ignoring previous versions
# Run full test suite
virtualenv --system-site-packages --python "${PYTHON}" "${MYTMPDIR}/botocore-recent"
source "${MYTMPDIR}/botocore-recent/bin/activate"
$PYTHON -m pip install 'botocore>=1.9.8' boto3
ansible-playbook -i ../../inventory -e @../../integration_config.yml -e @../../cloud-config-aws.yml -v playbooks/full_test.yml "$@"
