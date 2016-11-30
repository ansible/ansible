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
reorganize-tests.sh # temporary solution until repositories are merged

function cleanup
{
    if [ "$(ls test/results/coverage/)" ]; then
        ansible-test coverage xml --color -v --requirements
        cp -av test/results/reports/coverage.xml shippable/codecoverage/coverage.xml
    fi

    rmdir shippable/testresults/
    cp -av test/results/junit/ shippable/testresults/
}

trap cleanup EXIT

"test/utils/shippable/${script}.sh"
