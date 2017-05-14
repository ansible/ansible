#!/bin/bash -eux

set -o pipefail

# shellcheck disable=SC2086
ansible-test network-integration --explain ${CHANGED:+"$CHANGED"} 2>&1 | { grep ' network-integration: .* (targeted)$' || true; } > /tmp/network.txt

if [ "${COVERAGE}" ]; then
    # when on-demand coverage is enabled, force tests to run for all network platforms
    echo "coverage" > /tmp/network.txt
fi

target="network/ci/"

if [ -s /tmp/network.txt ]; then
    echo "Detected changes requiring integration tests specific to networking:"
    cat /tmp/network.txt

    echo "Running network integration tests for multiple platforms concurrently."

    # shellcheck disable=SC2086
    ansible-test network-integration --color -v --retry-on-error "${target}" --requirements ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
        --platform vyos/1.1.0 \
        --platform ios/csr1000v \

else
    echo "No changes requiring integration tests specific to networking were detected."
    echo "Running network integration tests for a single platform only."

    # shellcheck disable=SC2086
    ansible-test network-integration --color -v --retry-on-error "${target}" --requirements ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
        --platform vyos/1.1.0
fi
