#!/usr/bin/env bash

set -o pipefail -eu

"$@" 2>&1 | "$(dirname "$0")/timing.py"
