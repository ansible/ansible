#!/usr/bin/env bash

set -eux -o pipefail

export GIT_TOP_LEVEL SUBMODULE_DST

GIT_TOP_LEVEL="${WORK_DIR}/super/ansible_collections/ns/col"
SUBMODULE_DST="sub"

source collection-tests/git-common.bash
