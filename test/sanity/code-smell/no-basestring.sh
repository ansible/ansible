#!/bin/sh

BASEDIR=${1-"."}

# Not entirely correct but
# * basestring is still present and harmless in comments
# * basestring is also currently present in modules.  Porting of modules is more
#   of an Ansible 2.3 or greater goal.
BASESTRING_USERS=$(grep -r basestring $BASEDIR |grep isinstance| grep -v lib/ansible/compat/six/_six.py|grep -v lib/ansible/module_utils/six.py|grep -v lib/ansible/modules/core|grep -v lib/ansible/modules/extras)

if test -n "$BASESTRING_USERS" ; then
  printf "$BASESTRING_USERS"
  exit 1
else
  exit 0
fi
