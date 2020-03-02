#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

version="${args[1]}"
group="${args[2]}"

if [[ "${COVERAGE:-}" == "--coverage" ]]; then
    timeout=90
else
    timeout=30
fi

group1=()
group2=()
group3=()

# create three groups by putting network tests into separate groups
# add or remove network platforms as needed to balance the groups

networks2=(
    aireos
    avi
    check_point
    cloudvision
    dellos10
    dellos6
    dellos9
    eos
    f5
    fortimanager
    fortios
    ios
    iosxr
    ironware
    itential
    junos
    netact
    netscaler
    netvisor
    nos
    nso
)

networks3=(
    apconos
    aruba
    asa
    cloudengine
    cnos
    cumulus
    edgeos
    edgeswitch
    enos
    eric_eccli
    exos
    frr
    ftd
    icx
    ingate
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

for network in "${networks2[@]}"; do
    test_path="test/units/modules/network/${network}/"

    if [ -d "${test_path}" ]; then
        group1+=(--exclude "${test_path}")
        group2+=("${test_path}")
    fi
done

for network in "${networks3[@]}"; do
    test_path="test/units/modules/network/${network}/"

    if [ -d "${test_path}" ]; then
        group1+=(--exclude "${test_path}")
        group3+=("${test_path}")
    fi
done

case "${group}" in
    1) options=("${group1[@]:+${group1[@]}}") ;;
    2) options=("${group2[@]:+${group2[@]}}") ;;
    3) options=("${group3[@]:+${group3[@]}}") ;;
esac

if [ ${#options[@]} -eq 0 ] && [ "${group}" -gt 1 ]; then
    # allow collection migration unit tests for groups other than 1 to "pass" without updating shippable.yml or this script during migration
    echo "No unit tests found for group ${group}."
    exit
fi

ansible-test env --timeout "${timeout}" --color -v

# shellcheck disable=SC2086
ansible-test units --color -v --docker default --python "${version}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
    "${options[@]:+${options[@]}}" \
