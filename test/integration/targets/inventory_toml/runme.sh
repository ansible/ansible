#!/usr/bin/env bash

set -eux -o pipefail

source virtualenv.sh

for toml_library in tomli ""; do
    if [ "${toml_library}" ]; then
        pip install --disable-pip-version-check "${toml_library}"
    fi

    ansible-playbook -i inventory.toml playbook.yml "$@"

    if [ "${toml_library}" ]; then
        pip uninstall --disable-pip-version-check -y "${toml_library}"
    fi
done

echo "*** TEST PASS ***"
