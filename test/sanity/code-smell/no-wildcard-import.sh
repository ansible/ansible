#!/bin/sh

# Only needed until we enable pylint test for wildcard imports


# The first three paths here are valid uses of wildcard imports
# unsafe_proxy is backwards compat (pylint disabled added)
# module_common.py is picked up from static strings, not from actual imports (pylint won't detect)
# test_action.py is picked up from static strings, not from actual imports (pylint won't detect)
# mock.py is importing code for an installed library for compat (pylint disabled added)
# unittest.py is importing code for an installed library for compat (pylint disabled added)
#
# Everything else needs to be fixed
wildcard_imports=$(find . -path ./test/runner/.tox -prune \
        -o -path ./lib/ansible/vars/unsafe_proxy.py -prune \
        -o -path ./lib/ansible/executor/module_common.py -prune \
        -o -path ./test/units/plugins/action/test_action.py \
        -o -path ./lib/ansible/compat/tests/mock.py -prune \
        -o -path ./lib/ansible/compat/tests/unittest.py \
        -o -path ./lib/ansible/module_utils/api.py -prune \
        -o -path ./lib/ansible/module_utils/cloud.py -prune \
        -o -path ./lib/ansible/module_utils/aos.py -prune \
        -o -path ./test/units/modules/network/cumulus/test_nclu.py -prune \
        -o -path ./lib/ansible/modules/cloud/amazon -prune \
        -o -path ./lib/ansible/modules/cloud/openstack -prune \
        -o -path ./lib/ansible/modules/cloud/cloudstack -prune \
        -o -path ./lib/ansible/modules/monitoring -prune \
        -o -path ./lib/ansible/modules/network/f5 -prune \
        -o -path ./lib/ansible/modules/network/nxos -prune \
        -o -path ./lib/ansible/modules/packaging/os -prune \
        -o -name '*.py' -type f -exec grep -H 'import \*' '{}' '+')


if test -n "$wildcard_imports" ; then
  printf "\n== Wildcard imports detected ==\n"
  printf "%s" "$wildcard_imports"
  failures=$(printf "%s" "$wildcard_imports"| wc -l)
  failures=$((failures + 2))
  exit "$failures"
fi

exit 0
