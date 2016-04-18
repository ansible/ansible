#!/bin/bash -eux

source_root=$(python -c "from os import path; print(path.abspath(path.join(path.dirname('$0'), '../../..')))")

install_deps="${INSTALL_DEPS:-}"

cd "${source_root}"

if [ "${install_deps}" != "" ]; then
    apt-add-repository 'deb http://archive.ubuntu.com/ubuntu trusty-backports universe'
    apt-get update -qq
    apt-get install shellcheck

    pip install -r "${source_root}/test/utils/shippable/code-smell-requirements.txt" --upgrade
    pip list
fi

yamllint ./test

test/sanity/code-smell/replace-urlopen.sh
test/sanity/code-smell/use-compat-six.sh
test/sanity/code-smell/boilerplate.sh
test/sanity/code-smell/required-and-default-attributes.sh
test/sanity/code-smell/shebang.sh
test/sanity/code-smell/line-endings.sh
test/sanity/code-smell/empty-init.sh
test/sanity/code-smell/no-basestring.sh

shellcheck \
    test/integration/targets/*/*.sh \
    test/utils/shippable/*.sh
