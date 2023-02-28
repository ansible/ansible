#!/usr/bin/env bash
# Temporary script to support side-by-side testing for incidental code coverage.
# Once collection migration has been completed the incidental tests can be combined with the regular tests.

set -o pipefail -eux

declare -a args
IFS='/:' read -ra args <<< "$1"

script="${args[1]}"

IFS='/' test="${args[*]:1}"

".azure-pipelines/commands/incidental/${script}.sh" "${test}"
