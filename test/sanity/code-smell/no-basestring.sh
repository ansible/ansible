#!/bin/sh

BASEDIR=${1-"."}

# Not entirely correct but
# * basestring is still present and harmless in comments
# * basestring is also currently present in modules.  Porting of modules is more
#   of an Ansible 2.3 or greater goal.
BASESTRING_USERS=$(grep -r basestring "${BASEDIR}" \
    | grep isinstance \
    | grep -v \
    -e lib/ansible/compat/six/_six.py \
    -e lib/ansible/module_utils/six.py \
    -e lib/ansible/modules/core \
    -e lib/ansible/modules/extras \
    -e '/.tox/' \
    )

if test -n "${BASESTRING_USERS}"; then
  printf "%s" "${BASESTRING_USERS}"
  exit 1
else
  exit 0
fi
