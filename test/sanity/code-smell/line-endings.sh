#!/bin/sh

grep -RIPl '\r' . 2>/dev/null \
    --exclude-dir .git \
    | grep -v -E \
    -e '/.tox/' \
    | grep -v -F \
    -e './test/integration/targets/win_regmerge/templates/win_line_ending.j2'

if [ $? -ne 1 ]; then
    printf 'One or more file(s) listed above have invalid line endings.\n'
    printf 'Make sure all files use "\\n" for line endings instead of "\\r\\n".\n'
    exit 1
fi
