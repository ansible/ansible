#!/bin/sh

metaclass=$(find ./lib/ansible -path ./lib/ansible/modules/core -prune \
        -o -path ./lib/ansible/modules/extras -prune \
        -o -path ./lib/ansible/module_utils -prune \
        -o -path ./lib/ansible/compat/six/_six.py -prune \
        -o -path ./lib/ansible/utils/module_docs_fragments -prune \
        -o -name '*.py' -exec grep -HL '__metaclass__ = type' \{\} \;)

future=$(find ./lib/ansible -path ./lib/ansible/modules/core -prune \
        -o -path ./lib/ansible/modules/extras -prune \
        -o -path ./lib/ansible/module_utils -prune \
        -o -path ./lib/ansible/compat/six/_six.py -prune \
        -o -path ./lib/ansible/utils/module_docs_fragments -prune \
        -o -name '*.py' -exec grep -HL 'from __future__ import (absolute_import, division, print_function)' \{\} \;)

### TODO:
### - contrib/
### - module_utils that are py2.6+


if test -n "$metaclass" ; then
printf "\n== Missing __metaclass__ = type ==\n"
fi

if test -n "$metaclass" ; then
  printf "$metaclass\n"
fi

if test -n "$future" ; then
  printf "\n== Missing from __future__ import (absolute_import, division, print_function) ==\n"
fi

if test -n "$future" ; then
  printf "$future\n"
fi

if test -n "$future$metaclass" ; then
  failures=$(printf "$future$metaclass"| wc -l)
  failures=$(expr $failures + 2)
  exit $failures
fi
exit 0
