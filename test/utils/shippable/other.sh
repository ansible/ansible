#!/bin/bash -eux

set -o pipefail

shippable.py

echo '{"verified": false, "results": []}' > test/results/bot/ansible-test-failure.json

if [ "${BASE_BRANCH:-}" ]; then
    base_branch="origin/${BASE_BRANCH}"
else
    base_branch=""
fi
# shellcheck disable=SC2086
ansible-test compile --failure-ok --color -v --junit --coverage ${CHANGED:+"$CHANGED"} --docker default
# shellcheck disable=SC2086
ansible-test sanity  --failure-ok --color -v --junit --coverage ${CHANGED:+"$CHANGED"} --docker default --docker-keep-git --base-branch "${base_branch}"

rm test/results/bot/ansible-test-failure.json

if find test/results/bot/ -mindepth 1 -name '.*' -prune -o -print -quit | grep -q .; then
    echo "One or more of the above tests reported at least one failure."
    exit 1
fi
