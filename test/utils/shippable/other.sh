#!/bin/bash -eux

set -o pipefail

add-apt-repository 'deb http://archive.ubuntu.com/ubuntu trusty-backports universe'
add-apt-repository 'ppa:fkrull/deadsnakes'
add-apt-repository 'ppa:jonathonf/python-3.6'

apt-get update -qq
apt-get install -qq \
    shellcheck \
    python2.4 \
    python3.6 \

pip install tox --disable-pip-version-check

ansible-test compile --color -v
ansible-test sanity --color -v --tox --skip-test ansible-doc --python 2.7
ansible-test sanity --color -v --tox --test ansible-doc --coverage
