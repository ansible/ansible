#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

version="${args[1]}"
group="${args[2]}"

if [[ "${COVERAGE:-}" == "--coverage" ]]; then
    timeout=75
else
    timeout=15
fi

group1=()
group2=()

# create two groups by putting long running network tests into one group
# add or remove more network platforms as needed to balance the two groups

networks=(
    f5
    fortimanager
    fortios
    ios
    junos
    netact
    netscaler
    netvisor
    nos
    nso
    nuage
    nxos
    onyx
    opx
    ovs
    radware
    routeros
    slxos
    voss
    vyos
)

for network in "${networks[@]}"; do
    test_path="test/units/modules/network/${network}/"

    if [ -d "${test_path}" ]; then
        group1+=(--exclude "${test_path}")
        group2+=("${test_path}")
    fi
done

case "${group}" in
    1) options=("${group1[@]:+${group1[@]}}") ;;
    2) options=("${group2[@]:+${group2[@]}}") ;;
esac

if [ ${#options[@]} -eq 0 ] && [ "${group}" -eq 2 ]; then
    # allow collection migration unit tests for group 2 to "pass" without updating shippable.yml or this script during migration
    echo "No unit tests found for group ${group}."
    exit
fi

ansible-test env --timeout "${timeout}" --color -v

# shellcheck disable=SC2086
ansible-test units --color -v --docker default --python "${version}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
    "${options[@]:+${options[@]}}" \
