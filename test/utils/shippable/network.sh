#!/bin/bash -eux

set -o pipefail

ansible-test network-integration --explain 2>&1 | { grep ' network-integration: .* (targeted)$' || true; } > /tmp/network.txt

target="network/ci/"

if [ -s /tmp/network.txt ]; then
    echo "Detected changes requiring integration tests specific to networking:"
    cat /tmp/network.txt

    echo "Running network integration tests for multiple platforms concurrently."

    ansible-test network-integration --color -v --retry-on-error "${target}" --requirements \
        --platform vyos/1.1.0 \
        --platform ios/csr1000v \

else
    echo "No changes requiring integration tests specific to networking were detected."
    echo "Running network integration tests for a single platform only."

    ansible-test network-integration --color -v --retry-on-error "${target}" --requirements \
        --platform vyos/1.1.0
fi
