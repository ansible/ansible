#!/bin/sh

metaclass1=$(find ./bin -type f -exec grep -HL '__metaclass__ = type' '{}' '+')
future1=$(find ./bin -type f -exec grep -HL 'from __future__ import (absolute_import, division, print_function)' '{}' '+')

metaclass2=$(find ./lib/ansible -path ./lib/ansible/modules -prune \
        -o -path ./lib/ansible/module_utils -prune \
        -o -path ./lib/ansible/module_utils/six/_six.py -prune \
        -o -path ./lib/ansible/compat/selectors/_selectors2.py -prune \
        -o -path ./lib/ansible/utils/module_docs_fragments -prune \
        -o -name '*.py' -type f -size +0c -exec grep -HL '__metaclass__ = type' '{}' '+')

future2=$(find ./lib/ansible -path ./lib/ansible/modules -prune \
        -o -path ./lib/ansible/module_utils -prune \
        -o -path ./lib/ansible/module_utils/six/_six.py -prune \
        -o -path ./lib/ansible/compat/selectors/_selectors2.py -prune \
        -o -path ./lib/ansible/utils/module_docs_fragments -prune \
        -o -name '*.py' -type f -size +0c -exec grep -HL 'from __future__ import (absolute_import, division, print_function)' '{}' '+')

# Eventually we want metaclass3 and future3 to get down to 0
metaclass3=$(find ./lib/ansible/modules -path ./lib/ansible/modules/windows -prune \
        -o -path ./lib/ansible/modules/source_control -prune \
        -o -path ./lib/ansible/modules/packaging -prune \
        -o -path ./lib/ansible/modules/notification -prune \
        -o -path ./lib/ansible/modules/network -prune \
        -o -path ./lib/ansible/modules/net_tools -prune \
        -o -path ./lib/ansible/modules/monitoring -prune \
        -o -path ./lib/ansible/modules/messaging -prune \
        -o -path ./lib/ansible/modules/inventory -prune \
        -o -path ./lib/ansible/modules/identity -prune \
        -o -path ./lib/ansible/modules/files -prune \
        -o -path ./lib/ansible/modules/database -prune \
        -o -path ./lib/ansible/modules/crypto -prune \
        -o -path ./lib/ansible/modules/commands -prune \
        -o -path ./lib/ansible/modules/clustering -prune \
        -o -path ./lib/ansible/modules/cloud/webfaction -prune \
        -o -path ./lib/ansible/modules/cloud/vmware -prune \
        -o -path ./lib/ansible/modules/cloud/rackspace -prune \
        -o -path ./lib/ansible/modules/cloud/ovirt -prune \
        -o -path ./lib/ansible/modules/cloud/openstack -prune \
        -o -path ./lib/ansible/modules/cloud/misc -prune \
        -o -path ./lib/ansible/modules/cloud/google -prune \
        -o -path ./lib/ansible/modules/cloud/docker -prune \
        -o -path ./lib/ansible/modules/cloud/digital_ocean -prune \
        -o -path ./lib/ansible/modules/cloud/cloudstack -prune \
        -o -path ./lib/ansible/modules/cloud/centurylink -prune \
        -o -path ./lib/ansible/modules/cloud/amazon -prune \
        -o -name '*.py' -type f -size +0c -exec grep -HL '__metaclass__ = type' '{}' '+')

future3=$(find ./lib/ansible/modules -path ./lib/ansible/modules/windows -prune \
        -o -path ./lib/ansible/modules/source_control -prune \
        -o -path ./lib/ansible/modules/packaging -prune \
        -o -path ./lib/ansible/modules/notification -prune \
        -o -path ./lib/ansible/modules/network -prune \
        -o -path ./lib/ansible/modules/net_tools -prune \
        -o -path ./lib/ansible/modules/monitoring -prune \
        -o -path ./lib/ansible/modules/messaging -prune \
        -o -path ./lib/ansible/modules/inventory -prune \
        -o -path ./lib/ansible/modules/identity -prune \
        -o -path ./lib/ansible/modules/files -prune \
        -o -path ./lib/ansible/modules/database -prune \
        -o -path ./lib/ansible/modules/crypto -prune \
        -o -path ./lib/ansible/modules/commands -prune \
        -o -path ./lib/ansible/modules/clustering -prune \
        -o -path ./lib/ansible/modules/cloud/webfaction -prune \
        -o -path ./lib/ansible/modules/cloud/vmware -prune \
        -o -path ./lib/ansible/modules/cloud/rackspace -prune \
        -o -path ./lib/ansible/modules/cloud/ovirt -prune \
        -o -path ./lib/ansible/modules/cloud/openstack -prune \
        -o -path ./lib/ansible/modules/cloud/misc -prune \
        -o -path ./lib/ansible/modules/cloud/google -prune \
        -o -path ./lib/ansible/modules/cloud/docker -prune \
        -o -path ./lib/ansible/modules/cloud/digital_ocean -prune \
        -o -path ./lib/ansible/modules/cloud/cloudstack -prune \
        -o -path ./lib/ansible/modules/cloud/centurylink -prune \
        -o -path ./lib/ansible/modules/cloud/amazon -prune \
        -o -name '*.py' -type f -size +0c -exec egrep -HL 'from __future__ import (?absolute_import, division, print_function)?' '{}' '+')

### TODO:
### - contrib/
### - module_utils


if test -n "$metaclass1" -o -n "$metaclass2" -o -n "$metaclass3" ; then
printf "\n== Missing __metaclass__ = type ==\n"
fi

if test -n "$metaclass1" ; then
  printf "$metaclass1\n"
fi
if test -n "$metaclass2" ; then
  printf "$metaclass2\n"
fi
if test -n "$metaclass3" ; then
  printf "$metaclass3\n"
fi

if test -n "$future1" -o -n "$future2" -o -n "$future3" ; then
  printf "\n== Missing from __future__ import (absolute_import, division, print_function) ==\n"
fi

if test -n "$future1" ; then
  printf "$future1\n"
fi
if test -n "$future2" ; then
  printf "$future2\n"
fi
if test -n "$future3" ; then
  printf "$future3\n"
fi

if test -n "$future1$future2$future3$metaclass1$metaclass2$metaclass3" ; then
  failures=$(printf "$future1$future2$future3$metaclass1$metaclass2$metaclass3"| wc -l)
  failures=$(expr $failures + 2)
  exit $failures
fi
exit 0
