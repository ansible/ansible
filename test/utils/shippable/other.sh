#!/bin/bash -eux

set -o pipefail

add-apt-repository 'deb http://archive.ubuntu.com/ubuntu trusty-backports universe'
add-apt-repository 'ppa:ubuntu-toolchain-r/test'
add-apt-repository 'ppa:fkrull/deadsnakes'

apt-get update -qq
apt-get install -qq \
    shellcheck \
    python2.4 \
    g++-4.9 \
    python3.6-dev \

ln -sf x86_64-linux-gnu-gcc-4.9 /usr/bin/x86_64-linux-gnu-gcc

pip install tox --disable-pip-version-check

ansible-test compile --color -v
ansible-test sanity --color -v --tox --skip-test ansible-doc --python 2.7
ansible-test sanity --color -v --tox --test ansible-doc --coverage
