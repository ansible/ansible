#!/bin/bash -eux

set -o pipefail

source_root=$(python -c "from os import path; print(path.abspath(path.join(path.dirname('$0'), '../../..')))")

"${source_root}/test/utils/shippable/${TEST}.sh" 2>&1 | gawk '{ print strftime("%Y-%m-%d %H:%M:%S"), $0; fflush(); }'
