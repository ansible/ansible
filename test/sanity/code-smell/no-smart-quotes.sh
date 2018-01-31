#!/bin/sh

# shellcheck disable=SC1015,SC1016
egrep -r '[‘’“”]' . \
    --exclude-dir .git \
    --exclude-dir .tox \
    --exclude-dir __pycache__ \
    | grep -v \
    -e './test/sanity/code-smell/no-smart-quotes.sh' \
    -e './docs/docsite/rst/dev_guide/testing/sanity/no-smart-quotes.rst' \
    -e './test/integration/targets/unicode/unicode.yml' \
    -e '\.doctree matches$' \
    -e '\.pickle matches$' \
    -e './docs/docsite/_build/html/'

if [ $? -ne 1 ]; then
    printf 'The file(s) listed above have non-ascii quotes.\n'
    # shellcheck disable=SC1015,SC1016
    printf 'Make sure all files use " and '"'"' as quotation marks\n'
    printf 'These sed commands may be of help to you:\n'
    # shellcheck disable=SC1015,SC1016
    printf "  sed 's/[”“]/\"/g' \$FILENAME -i && sed \"s/[‘’]/'/g\" \$FILENAME -i\\n"
    exit 1
fi
