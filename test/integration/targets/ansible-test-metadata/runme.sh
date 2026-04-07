#!/usr/bin/env bash
# Verify that importlib.metadata can find ansible-core using the PYTHONPATH set by ansible-test.
# Regression test for https://github.com/ansible/ansible/issues/86695

set -eux

VERSION=$(python -c "from importlib.metadata import version; print(version('ansible-core'))")

test "$VERSION" = "$ANSIBLE_TEST_ANSIBLE_VERSION"
