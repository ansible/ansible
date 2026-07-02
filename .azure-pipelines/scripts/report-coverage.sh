#!/usr/bin/env bash
# Generate code coverage reports for uploading to Azure Pipelines and codecov.io.

set -o pipefail -eu

PATH="${PWD}/bin:${PATH}"

if ! ansible-test --help >/dev/null 2>&1; then
    # Install the devel version of ansible-test for generating code coverage reports.
    # This is only used by Ansible Collections, which are typically tested against multiple Ansible versions (in separate jobs).
    # Since a version of ansible-test is required that can work the output from multiple older releases, the devel version is used.
    pip install https://github.com/ansible/ansible/archive/devel.tar.gz --disable-pip-version-check
fi

# Generate stubs using docker.
# The use of docker is mandatory when Powershell code is present.
ansible-test coverage xml --group-by command --stub --docker --color -v
