#!/bin/bash -eux

set -o pipefail

pip install tox --disable-pip-version-check

ansible-test units --color -v --tox --coverage
