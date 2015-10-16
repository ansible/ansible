#!/bin/sh

BASEDIR=${1-"."}

URLLIB_USERS=$(find "$BASEDIR" -name '*.py' -exec grep -H urlopen \{\} \;)
URLLIB_USERS=$(echo "$URLLIB_USERS" | sed '/\(\n\|lib\/ansible\/module_utils\/urls.py\|lib\/ansible\/compat\/six\/_six.py\)/d')
if test -n "$URLLIB_USERS" ; then
  printf "$URLLIB_USERS"
  exit 1
else
  exit 0
fi
