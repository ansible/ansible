#!/bin/sh

# We're getting rid of get_exception in our code so that we can deprecate it.
# get_exception is no longer needed as we no longer support python-2.4 on the controller.

# We eventually want this list to be empty
get_exception=$(find . -path ./test/runner/.tox -prune \
        -o -path ./lib/ansible/module_utils -prune \
        -o -path ./lib/ansible/modules/storage/netapp -prune \
        -o -path ./lib/ansible/modules/packaging/os -prune \
        -o -path ./lib/ansible/modules/monitoring -prune \
        -o -path ./lib/ansible/modules/network/panos -prune \
        -o -path ./lib/ansible/modules/network/nxos -prune \
        -o -path ./lib/ansible/modules/network/junos -prune \
        -o -path ./lib/ansible/modules/network/vyos -prune \
        -o -path ./lib/ansible/modules/network/fortios -prune \
        -o -path ./lib/ansible/modules/network/f5 -prune \
        -o -path ./lib/ansible/modules/network/cloudengine -prune \
        -o -path ./lib/ansible/modules/network/aos -prune \
        -o -path ./lib/ansible/modules/network/eos -prune \
        -o -path ./lib/ansible/modules/files -prune \
        -o -path ./lib/ansible/modules/system -prune \
        -o -path ./lib/ansible/modules/web_infrastructure -prune \
        -o -path ./lib/ansible/plugins/action/wait_for_connection.py -prune \
        -o -name '*.py' -type f -exec grep -H 'get_exception' '{}' '+')


if test -n "$get_exception" ; then
  printf "\n== Contains get_exception() calls ==\n"
  printf "%s" "$get_exception"
  failures=$(printf "%s" "$get_exception"| wc -l)
  failures=$((failures + 2))
  exit "$failures"
fi

exit 0
