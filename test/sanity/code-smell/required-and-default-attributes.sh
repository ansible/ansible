#!/bin/sh

BASEDIR=${1-"lib/ansible"}
cd "$BASEDIR"
grep -r FieldAttribute . |grep 'default' | grep 'required'
if test $? -eq 0 ; then
    exit 1
fi
exit 0

