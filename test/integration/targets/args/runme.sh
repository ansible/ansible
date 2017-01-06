#!/usr/bin/env bash

set -eu

echo "arg[#]: $#"
echo "arg[0]: $0"

i=0
for arg in "$@"; do
    i=$((i+1))
    echo "arg[$i]: ${arg}"
done
