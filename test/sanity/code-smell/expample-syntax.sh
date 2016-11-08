#!/bin/bash

# Look through EXAMPLES in core modules for instanecs of key=value syntax
# Modules can be allowed to include this syntax style in the examples
# by adding to the WHITELIST_REGEXP

BASEDIR=${1-"lib/ansible/modules/core"}
WHITELIST_REGEXP="(.*command|mysql_user|.*lineinfile|synchronize|slurp)\.py"                     # Example: (win.*|apache2_mod_.*)\.py
FOUND=""
MODULES=$(find "$BASEDIR" -regextype posix-egrep -name '*.py' ! -regex ".*/$WHITELIST_REGEXP")

for module in $MODULES; do
    # Isolate lines between EXAMPLES ''' and ''', single or double quotes
    # Exclude lines with comments, ad-hoc commands, 'with_', and several other parameters
    test=$(sed -n "/EXAMPLES/,/\('''\|\"\"\"\)/p" "$module" | grep -Pv "(EXAMPLES|(^(\s+)?#)|(:.*?#)|(with_\w+:)|(^\s+-.*=)|((meta|nics|mode|body|url|name|key_options|src|command|shell):)|(\|\s+?\w+\(.*=.*\))|(^(\\$\s+)?ansible))" | grep -P '\w+=[^\s=]')
    if [ -n "$test" ] ; then
        FOUND="$FOUND#$module"
    fi
done

if [ -n "$FOUND" ] ; then
    echo "$FOUND" | tr '#' '\n'
    echo "One or more of the above modules uses the key=value syntax in the EXAMPLES section."
    echo "Please change the examples to use multi-line YAML."
    exit 1
fi

exit 0

