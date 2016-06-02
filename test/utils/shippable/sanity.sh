#!/bin/bash -eux

source_root=$(python -c "from os import path; print(path.abspath(path.join(path.dirname('$0'), '../../..')))")

install_deps="${INSTALL_DEPS:-}"

cd "${source_root}"

if [ "${TOXENV}" = 'py24' ]; then
    if [ "${install_deps}" != "" ]; then
        add-apt-repository ppa:fkrull/deadsnakes && apt-get update -qq && apt-get install python2.4 -qq
    fi

    python2.4 -V
    python2.4 -m compileall -fq -x 'module_utils/(a10|rax|openstack|ec2|gce|docker_common|azure_rm_common|vca|vmware).py' lib/ansible/module_utils
else
    if [ "${install_deps}" != "" ]; then
        pip install tox
    fi

    xunit_dir="${source_root}/shippable/testresults"
    coverage_dir="${source_root}/shippable/codecoverage"

    mkdir -p "${xunit_dir}"
    mkdir -p "${coverage_dir}"

    xunit_file="${xunit_dir}/nosetests-xunit.xml"
    coverage_file="${coverage_dir}/nosetests-coverage.xml"

    TOX_TESTENV_PASSENV=NOSETESTS NOSETESTS="nosetests --with-xunit --xunit-file='${xunit_file}' --cover-xml --cover-xml-file='${coverage_file}'" tox
fi
