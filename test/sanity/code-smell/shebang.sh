#!/bin/sh

grep '^#!' -rIn . \
    --exclude-dir .git \
    --exclude-dir .tox \
    | grep ':1:' | sed 's/:1:/:/' | grep -v -E \
    -e '^\./lib/ansible/modules/' \
    -e '^\./test/integration/targets/[^/]*/library/[^/]*:#!powershell$' \
    -e '^\./test/sanity/validate-modules/validate-modules:#!/usr/bin/env python2$' \
    -e ':#!/bin/sh$' \
    -e ':#!/bin/bash( -[eux]|$)' \
    -e ':#!/usr/bin/make -f$' \
    -e ':#!/usr/bin/env python$' \
    -e ':#!/usr/bin/env bash$' \
    -e ':#!/usr/bin/env fish$'

if [ $? -ne 1 ]; then
    echo "One or more file(s) listed above have an unexpected shebang."
    echo "See $0 for the list of acceptable values."
    exit 1
fi
