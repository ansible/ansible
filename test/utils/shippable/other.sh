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

echo '{"verified": false, "results": []}' > test/results/bot/ansible-test-failure.json

ansible-test compile --failure-ok --color -v --junit --requirements
ansible-test sanity  --failure-ok --color -v --junit --tox --skip-test ansible-doc --python 2.7
ansible-test sanity  --failure-ok --color -v --junit --tox --test ansible-doc --coverage

rm test/results/bot/ansible-test-failure.json

if find test/results/bot/ -mindepth 1 -name '.*' -prune -o -print -quit | grep -q .; then
    echo "One or more of the above ansible-test commands recorded at least one test failure."
    exit 1
fi
