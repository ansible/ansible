#!/bin/bash -eux

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "${TEST}"

version="${args[1]}"

if [ "${version}" = "3.6" ]; then
    retry.py add-apt-repository 'ppa:ubuntu-toolchain-r/test'
    retry.py add-apt-repository 'ppa:fkrull/deadsnakes'

    retry.py apt-get update -qq
    retry.py apt-get install -qq \
        g++-4.9 \
        python3.6-dev \

    ln -sf x86_64-linux-gnu-gcc-4.9 /usr/bin/x86_64-linux-gnu-gcc
fi

retry.py pip install tox --disable-pip-version-check

ansible-test units --color -v --tox --coverage --python "${version}"
