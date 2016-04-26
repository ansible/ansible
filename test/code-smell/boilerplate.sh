#!/bin/sh

metaclass1=$(find ./bin -type f -exec grep -HL '__metaclass__ = type' \{\} \; )
future1=$(find ./bin -type f -exec grep -HL 'from __future__ import (absolute_import, division, print_function)' \{\} \;)

metaclass2=$(find ./lib/ansible -path ./lib/ansible/modules/core -prune \
        -o -path ./lib/ansible/modules/extras -prune \
        -o -path ./lib/ansible/module_utils -prune \
        -o -path ./lib/ansible/compat/six/_six.py -prune \
        -o -path ./lib/ansible/utils/module_docs_fragments -prune \
        -o -name '*.py' -exec grep -HL '__metaclass__ = type' \{\} \;)

future2=$(find ./lib/ansible -path ./lib/ansible/modules/core -prune \
        -o -path ./lib/ansible/modules/extras -prune \
        -o -path ./lib/ansible/module_utils -prune \
        -o -path ./lib/ansible/compat/six/_six.py -prune \
        -o -path ./lib/ansible/utils/module_docs_fragments -prune \
        -o -name '*.py' -exec grep -HL 'from __future__ import (absolute_import, division, print_function)' \{\} \;)

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
