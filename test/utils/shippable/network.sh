#!/bin/bash -eux

set -o pipefail

# shellcheck disable=SC2086
ansible-test network-integration --explain ${CHANGED:+"$CHANGED"} 2>&1 | { grep ' network-integration: .* (targeted)$' || true; } > /tmp/network.txt

if [ "${COVERAGE}" ]; then
    # when on-demand coverage is enabled, force tests to run for all network platforms
    echo "coverage" > /tmp/network.txt
fi

target="network/ci/"

# python versions to test in order
# all versions run full tests
python_versions=(
    2.7
)

if [ -s /tmp/network.txt ]; then
    echo "Detected changes requiring integration tests specific to networking:"
    cat /tmp/network.txt

    echo "Running network integration tests for multiple platforms concurrently."

    platforms=(
        --platform vyos/1.1.0
        --platform ios/csr1000v
    )
else
    echo "No changes requiring integration tests specific to networking were detected."
    echo "Running network integration tests for a single platform only."

    platforms=(
        --platform vyos/1.1.0
    )
fi

retry.py pip install tox --disable-pip-version-check

for version in "${python_versions[@]}"; do
    # clean up between test runs until we switch from --tox to --docker
    rm -rf ~/.ansible/{cp,pc,tmp}/

    # shellcheck disable=SC2086
    ansible-test network-integration --color -v --retry-on-error "${target}" --tox --python "${version}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
        "${platforms[@]}"
done
