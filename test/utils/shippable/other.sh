#!/bin/bash -eux

set -o pipefail

retry.py apt-get update -qq
retry.py apt-get install -qq \
    shellcheck \

retry.py pip install tox --disable-pip-version-check

echo '{"verified": false, "results": []}' > test/results/bot/ansible-test-failure.json

ansible-test compile --failure-ok --color -v --junit --requirements
ansible-test sanity  --failure-ok --color -v --junit --tox --skip-test ansible-doc --python 3.5
ansible-test sanity  --failure-ok --color -v --junit --tox --test ansible-doc --coverage

rm test/results/bot/ansible-test-failure.json

if find test/results/bot/ -mindepth 1 -name '.*' -prune -o -print -quit | grep -q .; then
    echo "One or more of the above ansible-test commands recorded at least one test failure."
    exit 1
fi
