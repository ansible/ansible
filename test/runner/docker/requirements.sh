#!/bin/bash -eu

python_versions=(
    2.6
    2.7
    3.5
    3.6
)

requirements=()

for requirement in *.txt; do
    if [ "${requirement}" != "constraints.txt" ]; then
        requirements+=("-r" "${requirement}")
    fi
done

for python_version in "${python_versions[@]}"; do
    set -x
    "python${python_version}" /tmp/get-pip.py -c constraints.txt
    "pip${python_version}" install --disable-pip-version-check -c constraints.txt "${requirements[@]}"
    set +x
done
