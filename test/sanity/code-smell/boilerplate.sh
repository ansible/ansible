#!/bin/sh

metaclass1=$(git ls-files bin/ | xargs grep -HL '__metaclass__ = type')
future1=$(git ls-files bin/ | xargs grep -HL 'from __future__ import (absolute_import, division, print_function)')

py_files=$(git ls-files lib/ansible | grep '.*\.py$'| \
           grep -v \
           -e 'lib/ansible/modules/' \
           -e 'lib/ansible/utils/module_docs' \
           -e 'lib/ansible/module_utils/' \
           -e 'lib/ansible/compat/selectors/_selectors2.py' \
           -e 'lib/ansible/compat/six')

metaclass2=$(echo "${py_files}" | xargs grep -HL '__metaclass__ = type')
future2=$(echo "${py_files}" | xargs grep -HL 'from __future__ import (absolute_import, division, print_function)')

### TODO:
### - contrib/
### - module_utils that are py2.6+


if test -n "$metaclass1" -o -n "$metaclass2" ; then
printf "\n== Missing __metaclass__ = type ==\n"
fi

if test -n "$metaclass1" ; then
  printf "$metaclass1\n"
fi
if test -n "$metaclass2" ; then
  printf "$metaclass2\n"
fi

if test -n "$future1" -o -n "$future2" ; then
  printf "\n== Missing from __future__ import (absolute_import, division, print_function) ==\n"
fi

if test -n "$future1" ; then
  printf "$future1\n"
fi
if test -n "$future2" ; then
  printf "$future2\n"
fi

if test -n "$future1$future2$metaclass1$metaclass2" ; then
  failures=$(printf "$future1$future2$metaclass1$metaclass2"| wc -l)
  failures=$(expr $failures + 2)
  exit $failures
fi
exit 0
