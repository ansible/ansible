#!/bin/bash -eux

source_root=$(python -c "from os import path; print(path.abspath(path.join(path.dirname('$0'), '../../..')))")

install_deps="${INSTALL_DEPS:-}"

cd "${source_root}"

if [ "${install_deps}" != "" ]; then
    add-apt-repository ppa:fkrull/deadsnakes
    apt-add-repository 'deb http://archive.ubuntu.com/ubuntu trusty-backports universe'
    apt-get update -qq

    apt-get install -qq shellcheck python2.4

    pip install git+https://github.com/ansible/ansible.git@devel#egg=ansible
    pip install git+https://github.com/sivel/ansible-testing.git#egg=ansible_testing
fi

python2.4 -m compileall -fq   -i                    "test/utils/shippable/sanity-test-python24.txt"
python2.4 -m compileall -fq   -x "($(printf %s "$(< "test/utils/shippable/sanity-skip-python24.txt"))" | tr '\n' '|')" .
python2.6 -m compileall -fq .
python2.7 -m compileall -fq .
python3.5 -m compileall -fq . -x "($(printf %s "$(< "test/utils/shippable/sanity-skip-python3.txt"))"  | tr '\n' '|')"

ANSIBLE_DEPRECATION_WARNINGS=false \
    ansible-validate-modules --exclude '/utilities/|/shippable(/|$)' .

shellcheck \
    test/utils/shippable/*.sh
