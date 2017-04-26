#!/bin/bash -eux

source_root=$(python -c "from os import path; print(path.abspath(path.join(path.dirname('$0'), '../../..')))")

install_deps="${INSTALL_DEPS:-}"

cd "${source_root}"

if [ "${install_deps}" != "" ]; then
    apt-get update -qq
    apt-get install shellcheck

    pip install -r "${source_root}/test/utils/shippable/code-smell-requirements.txt" --upgrade
    pip list
fi

yamllint .
test/code-smell/replace-urlopen.sh .
test/code-smell/use-compat-six.sh lib
test/code-smell/boilerplate.sh
test/code-smell/required-and-default-attributes.sh

shellcheck \
    test/utils/shippable/*.sh
