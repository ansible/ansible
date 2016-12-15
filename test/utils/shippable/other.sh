#!/bin/bash -eux

set -o pipefail

add-apt-repository 'deb http://archive.ubuntu.com/ubuntu trusty-backports universe'
add-apt-repository 'ppa:fkrull/deadsnakes'

apt-get update -qq
apt-get install python2.4 shellcheck -qq

pip install tox --disable-pip-version-check

ansible-test compile --color -v
ansible-test sanity --color -v --tox --skip-test ansible-doc --python 2.7
ansible-test sanity --color -v --tox --test ansible-doc --coverage
