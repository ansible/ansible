#!/bin/sh

# Do we want to check dynamic inventory, bin, etc?
BASEDIR=${1-"lib"}

SIX_USERS=$(find "$BASEDIR" -name '*.py' -exec grep -H six \{\} \;|grep import |grep -v ansible.compat)
if test -n "$SIX_USERS" ; then
  printf "$SIX_USERS"
  exit 1
else
  exit 0
fi
