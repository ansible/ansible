#!/usr/bin/env bash

set -eux -o pipefail


export PIP_DISABLE_PIP_VERSION_CHECK=1


source virtualenv.sh


>&2 echo '=== Test that the module gets picked up if discoverable via PYTHONPATH env var ==='
PYTHONPATH="${PWD}/ansible-collection-python-dist-boo:$PYTHONPATH" \
ansible \
    -m python.dist.boo \
    -a 'name=Bob' \
    -c local localhost \
    "$@" | grep -E '"greeting": "Hello, Bob!",'


>&2 echo '=== Test that the module gets picked up if installed into site-packages ==='
python -m pip install build
( # Build a binary Python dist (a wheel) using build:
  cp -r ansible-collection-python-dist-boo "${OUTPUT_DIR}/"
  cd "${OUTPUT_DIR}/ansible-collection-python-dist-boo"
  python -m build -w -o dist .
)
# Install a pre-built dist with pip:
python -m pip install \
  --no-index \
  -f "${OUTPUT_DIR}/ansible-collection-python-dist-boo/dist/" \
  --only-binary=ansible-collections.python.dist \
  ansible-collections.python.dist
python -m pip show ansible-collections.python.dist
ansible \
    -m python.dist.boo \
    -a 'name=Frodo' \
    -c local localhost \
    "$@" | grep -E '"greeting": "Hello, Frodo!",'


>&2 echo '=== Test that ansible_collections root takes precedence over PYTHONPATH/site-packages ==='
# This is done by injecting a module with the same FQCN
# into another collection root.
ANSIBLE_COLLECTIONS_PATH="${PWD}/ansible-collection-python-dist-foo" \
PYTHONPATH="${PWD}/ansible-collection-python-dist-boo:$PYTHONPATH" \
ansible \
    -m python.dist.boo \
    -a 'name=Степан' \
    -c local localhost \
    "$@" | grep -E '"greeting": "Привіт, Степан!",'
