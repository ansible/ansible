#!/bin/bash -eux

set -o pipefail

retry.py add-apt-repository 'deb http://archive.ubuntu.com/ubuntu trusty-backports universe'
retry.py add-apt-repository 'ppa:ubuntu-toolchain-r/test'
retry.py add-apt-repository 'ppa:fkrull/deadsnakes'

retry.py apt-get update -qq
retry.py apt-get install -qq \
    shellcheck \
    python2.4 \
    g++-4.9 \
    python3.6-dev \

ln -sf x86_64-linux-gnu-gcc-4.9 /usr/bin/x86_64-linux-gnu-gcc

retry.py pip install tox --disable-pip-version-check

errors=0

set +e

ansible-test compile --color -v --junit --requirements || ((errors++))
ansible-test sanity --color -v --junit --tox --skip-test ansible-doc --python 2.7 || ((errors++))
ansible-test sanity --color -v --junit --tox --test ansible-doc --coverage || ((errors++))

set -e

if [ ${errors} -gt 0 ]; then
    echo "${errors} of the above ansible-test command(s) failed."
    exit 1
fi
