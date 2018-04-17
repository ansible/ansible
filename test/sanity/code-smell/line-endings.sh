#!/bin/sh

grep -rIPl '\r' . \
    --exclude-dir .git \
    --exclude-dir .tox \
    | grep -v -F \
    -e './test/integration/targets/template/files/foo.dos.txt' \
    -e './test/integration/targets/win_regmerge/templates/win_line_ending.j2' \
    -e './test/integration/targets/win_template/files/foo.dos.txt' \
    -e './test/integration/targets/win_module_utils/library/legacy_only_new_way_win_line_endings.ps1' \
    -e './test/integration/targets/win_module_utils/library/legacy_only_old_way_win_line_endings.ps1' \

if [ $? -ne 1 ]; then
    printf 'One or more file(s) listed above have invalid line endings.\n'
    printf 'Make sure all files use "\\n" for line endings instead of "\\r\\n".\n'
    exit 1
fi
