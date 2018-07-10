#!/bin/bash -eux

set -o pipefail

"$@" 2>&1 | gawk '{ print strftime("%Y-%m-%d %H:%M:%S"), $0; fflush(); }'
