#!/bin/sh

# We're getting rid of get_exception in our code so that we can deprecate it.
# get_exception is no longer needed as we no longer support python-2.4 on the controller.

# We eventually want pycompat24 and basic.py to be the only things on this list
get_exception=$(find . -path ./test/runner/.tox -prune \
        -o -path ./lib/ansible/module_utils/pycompat24.py -prune \
        -o -path ./lib/ansible/module_utils/basic.py -prune \
        -o -path ./lib/ansible/modules/network/panos -prune \
        -o -path ./lib/ansible/modules/network/junos/junos_facts.py -prune \
        -o -path ./lib/ansible/modules/network/junos/junos_package.py -prune \
        -o -path ./lib/ansible/modules/network/cloudengine/ce_file_copy.py -prune \
        -o -path ./lib/ansible/modules/system -prune \
        -o -name '*.py' -type f -exec grep -H 'get_exception' '{}' '+')

basic_failed=0

if test "$(grep -c get_exception ./lib/ansible/module_utils/basic.py)" -gt 1 ; then
  printf "\n== basic.py contains get_exception calls ==\n\n"
  printf "  basic.py is allowed to import get_exception for backwards compat but\n"
  printf "  should not call it anywhere\n"
  basic_failed=1
fi

failures=0
if test -n "$get_exception" ; then
  printf "\n== Contains get_exception() calls ==\n"
  printf "  %s\n" "$get_exception"
  failures=$(printf "%s" "$get_exception"| wc -l)
  failures=$((failures + 2))
fi

exit $((basic_failed + failures))
