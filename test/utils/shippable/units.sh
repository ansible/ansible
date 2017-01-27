#!/bin/bash -eux

set -o pipefail

add-apt-repository 'ppa:ubuntu-toolchain-r/test'
add-apt-repository 'ppa:fkrull/deadsnakes'

apt-get update -qq
apt-get install -qq \
    g++-4.9 \
    python3.6-dev \

ln -sf x86_64-linux-gnu-gcc-4.9 /usr/bin/x86_64-linux-gnu-gcc

pip install tox --disable-pip-version-check

ansible-test units --color -v --tox --coverage
