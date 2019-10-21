#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

version="${args[1]}"
group="${args[2]}"

if [[ "${COVERAGE:-}" == "--coverage" ]]; then
    timeout=60
else
    timeout=11
fi

group1=()
group2=()
group3=()

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

group3_networks=(
    f5
    fortios
    fortimanager
    nxos
)

for network in "${networks[@]}"; do
    group1+=(--exclude "test/units/modules/network/${network}/")
    if [[ ! "${group3_networks[*]}" =~ $network ]]; then
        group2+=("test/units/modules/network/${network}/")
    else
        group3+=("test/units/modules/network/${network}/")
    fi
done

case "${group}" in
    1) options=("${group1[@]}") ;;
    2) options=("${group2[@]}") ;;
    3) options=("${group3[@]}") ;;
esac

ansible-test env --timeout "${timeout}" --color -v

# shellcheck disable=SC2086
ansible-test units --color -v --docker default --python "${version}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} \
    "${options[@]}" \
