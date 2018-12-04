#!/bin/bash -eu

set -o pipefail

"$@" 2>&1 | "$(dirname "$0")/timing.py"
