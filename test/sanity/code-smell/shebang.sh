#!/bin/sh

grep '^#!' -rIn . \
    --exclude-dir .git \
    --exclude-dir .tox \
    | grep ':1:' | sed 's/:1:/:/' | grep -v -E \
    -e '^\./lib/ansible/modules/' \
    -e '^\./test/integration/targets/[^/]*/library/[^/]*:#!powershell$' \
    -e '^\./test/integration/targets/[^/]*/library/[^/]*:#!/usr/bin/python$' \
    -e '^\./test/integration/targets/module_precedence/.*lib.*:#!/usr/bin/python$' \
    -e '^\./hacking/cherrypick.py:#!/usr/bin/env python3$' \
    -e ':#!/bin/sh$' \
    -e ':#!/bin/bash( -[eux]|$)' \
    -e ':#!/usr/bin/make -f$' \
    -e ':#!/usr/bin/env python$' \
    -e ':#!/usr/bin/env bash$' \
    -e ':#!/usr/bin/env fish$' \
    -e ':#!/usr/bin/env pwsh$' \

if [ $? -ne 1 ]; then
    echo "One or more file(s) listed above have an unexpected shebang."
    echo "See $0 for the list of acceptable values."
    exit 1
fi
