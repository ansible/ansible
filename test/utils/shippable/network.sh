#!/bin/bash -eux

set -o pipefail

# shellcheck disable=SC2086
ansible-test network-integration --explain ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} 2>&1 \
    | { grep ' network-integration: .* (targeted)$' || true; } > /tmp/network.txt

if [ "${COVERAGE}" ]; then
    # when on-demand coverage is enabled, force tests to run for all network platforms
    echo "coverage" > /tmp/network.txt
fi

target="shippable/network/"

stage="${S:-prod}"
provider="${P:-default}"

# python versions to test in order
# all versions run full tests
python_versions=(
    2.7
    3.6
)

if [ -s /tmp/network.txt ]; then
    echo "Detected changes requiring integration tests specific to networking:"
    cat /tmp/network.txt

    echo "Running network integration tests for multiple platforms concurrently."

    platforms=(
        --platform vyos/1.1.8
    )
else
    echo "No changes requiring integration tests specific to networking were detected."
    echo "Running network integration tests for a single platform only."

    platforms=(
        --platform vyos/1.1.8
    )
fi

for version in "${python_versions[@]}"; do
    # terminate remote instances on the final python version tested
    if [ "${version}" = "${python_versions[-1]}" ]; then
        terminate="always"
    else
        terminate="never"
    fi

    # shellcheck disable=SC2086
    ansible-test network-integration --color -v --retry-on-error "${target}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} \
         "${platforms[@]}" \
        --docker default --python "${version}" \
        --remote-terminate "${terminate}" --remote-stage "${stage}" --remote-provider "${provider}"
done
