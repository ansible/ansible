#!/bin/sh

# Only needed until we can enable a pylint test for this.  We may have to write
# one or add it to another existing test (like the one to warn on inappropriate
# variable names).  Adding to an existing test may be hard as we may have many
# other things that are not compliant with that test.


# Need to fix everything in the whitelist in order to enable a pylint test.
# We've settled on "dummy" as the variable to replace dummy variables with
# (vast majority of these cases)
#
# before enabling *this* test, we need to create a full list of files which we need to fix
# Can use the base find command to help generate that list
#   find . -name '*.py' -type f -exec egrep -H '( |[^C]\()_( |,|\))' \{\} \+
#
underscore_as_variable=$(find . -path ./test/runner/.tox -prune \
        -path ./contrib/inventory/gce.py \
        -o -name '*.py' -type f -exec egrep -H '( |[^C]\()_( |,|\))' \{\} \+ )


if test -n "$underscore_as_variable" ; then
  printf "\n== Underscore used as a variable ==\n"
  printf "%s" "$underscore_as_variable"
  failures=$(printf "%s" "$underscore_as_variable"| wc -l)
  failures=$((failures + 2))
  exit "$failures"
fi

exit 0
