#!/bin/bash -eux

set -o pipefail

declare -a args
IFS='/:' read -ra args <<< "$1"

script="${args[0]}"

test="$1"

docker images ansible/ansible
docker ps

for container in $(docker ps --format '{{.Image}} {{.ID}}' | grep -v '^drydock/' | sed 's/^.* //'); do
    docker rm -f "${container}"
done

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

if [ "${JOB_TRIGGERED_BY_NAME:-}" == "nightly-trigger" ]; then
    COVERAGE=yes
    COMPLETE=yes
fi

if [ -n "${COVERAGE:-}" ]; then
    # on-demand coverage reporting triggered by setting the COVERAGE environment variable to a non-empty value
    export COVERAGE="--coverage"
elif [[ "${COMMIT_MESSAGE}" =~ ci_coverage ]]; then
    # on-demand coverage reporting triggered by having 'ci_coverage' in the latest commit message
    export COVERAGE="--coverage"
else
    # on-demand coverage reporting disabled (default behavior, always-on coverage reporting remains enabled)
    export COVERAGE=""
fi

if [ -n "${COMPLETE:-}" ]; then
    # disable change detection triggered by setting the COMPLETE environment variable to a non-empty value
    export CHANGED=""
elif [[ "${COMMIT_MESSAGE}" =~ ci_complete ]]; then
    # disable change detection triggered by having 'ci_complete' in the latest commit message
    export CHANGED=""
else
    # enable change detection (default behavior)
    export CHANGED="--changed"
fi

if [ "${IS_PULL_REQUEST:-}" == "true" ]; then
    # run unstable tests which are targeted by focused changes on PRs
    export UNSTABLE="--allow-unstable-changed"
else
    # do not run unstable tests outside PRs
    export UNSTABLE=""
fi

# remove empty core/extras module directories from PRs created prior to the repo-merge
find lib/ansible/modules -type d -empty -print -delete

function cleanup
{
    if find test/results/coverage/ -mindepth 1 -name '.*' -prune -o -print -quit | grep -q .; then
        # for complete on-demand coverage generate a report for all files with no coverage on the "other" job so we only have one copy
        if [ "${COVERAGE}" ] && [ "${CHANGED}" == "" ] && [ "${test}" == "other" ]; then
            stub="--stub"
        else
            stub=""
        fi

        # shellcheck disable=SC2086
        ansible-test coverage xml --color -v --requirements --group-by command --group-by version ${stub:+"$stub"}
        cp -a test/results/reports/coverage=*.xml shippable/codecoverage/

        # upload coverage report to codecov.io only when using complete on-demand coverage
        if [ "${COVERAGE}" ] && [ "${CHANGED}" == "" ]; then
            for file in test/results/reports/coverage=*.xml; do
                flags="${file##*/coverage=}"
                flags="${flags%.xml}"
                flags="${flags//=/,}"
                flags="${flags//[^a-zA-Z0-9_,]/_}"

                bash <(curl -s https://codecov.io/bash) \
                    -f "${file}" \
                    -F "${flags}" \
                    -n "${test}" \
                    -t 83cd8957-dc76-488c-9ada-210dcea51633 \
                    -X coveragepy \
                    -X gcov \
                    -X fix \
                    -X search \
                    -X xcode \
                || echo "Failed to upload code coverage report to codecov.io: ${file}"
            done
        fi
    fi

    rmdir shippable/testresults/
    cp -a test/results/junit/ shippable/testresults/
    cp -a test/results/data/ shippable/testresults/
    cp -aT test/results/bot/ shippable/testresults/
}

trap cleanup EXIT

"test/utils/shippable/${script}.sh" "${test}"
