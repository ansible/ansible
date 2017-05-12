#!/bin/bash -eux

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "${TEST}"

script="${args[0]}"

docker images ansible/ansible
docker ps

if [ -d /home/shippable/cache/ ]; then
    ls -la /home/shippable/cache/
fi

which python
python -V

which pip
pip --version
pip list --disable-pip-version-check

export PATH="test/runner:${PATH}"
export PYTHONIOENCODING='utf-8'

# remove empty core/extras module directories from PRs created prior to the repo-merge
find lib/ansible/modules -type d -empty -print -delete

function cleanup
{
    if find test/results/coverage/ -mindepth 1 -name '.*' -prune -o -print -quit | grep -q .; then
        ansible-test coverage xml --color -v --requirements
        cp -a test/results/reports/coverage.xml shippable/codecoverage/coverage.xml
    fi

    rmdir shippable/testresults/
    cp -a test/results/junit/ shippable/testresults/
    cp -aT test/results/bot/ shippable/testresults/
}

trap cleanup EXIT

"test/utils/shippable/${script}.sh"
