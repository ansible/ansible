#!/usr/bin/env bash

set -eux -o pipefail

export GIT_TOP_LEVEL SUBMODULE_DST

GIT_TOP_LEVEL="${WORK_DIR}/super"
SUBMODULE_DST="ansible_collections/ns/col/sub"

source collection-tests/git-common.bash
