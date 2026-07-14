#!/usr/bin/env bash

set -eux -o pipefail

source virtualenv.sh

for toml_library in tomli ""; do
    if [ "${toml_library}" ]; then
        pip install --disable-pip-version-check "${toml_library}"
    fi

    if [ "${ANSIBLE_TEST_PYTHON_VERSION}" = "3.10" ] && [ "${toml_library}" = "" ]; then
        if ansible-playbook -i inventory.toml playbook.yml "$@"; then
            echo "passed when it should have failed, is 'toml' or 'tomli' installed globally?"
            exit 1
        else
            echo failed as expected
        fi
    else
        ansible-playbook -i inventory.toml playbook.yml "$@"
    fi

    if [ "${toml_library}" ]; then
        pip uninstall --disable-pip-version-check -y "${toml_library}"
    fi
done

echo "*** TEST PASS ***"
