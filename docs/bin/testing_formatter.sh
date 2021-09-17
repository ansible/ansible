#!/bin/sh

set -eux

FILENAME=../docsite/rst/dev_guide/testing/sanity/index.rst

cat <<- EOF >$FILENAME.new
.. _all_sanity_tests:

Sanity Tests
============

The following sanity tests are available as \`\`--test\`\` options for \`\`ansible-test sanity\`\`.
This list is also available using \`\`ansible-test sanity --list-tests --allow-disabled\`\`.

For information on how to run these tests, see :ref:\`sanity testing guide <testing_sanity>\`.

.. toctree::
   :maxdepth: 1

$(for test in $(../../bin/ansible-test sanity --list-tests --allow-disabled); do echo "   ${test}"; done)

EOF

# By default use sha1sum which exists on Linux, if not present select the correct binary
# based on platform defaults
SHA_CMD="sha1sum"
if ! command -v ${SHA_CMD} > /dev/null 2>&1; then
    if command -v sha1 > /dev/null 2>&1; then
        SHA_CMD="sha1"
    elif command -v shasum > /dev/null 2>&1; then
        SHA_CMD="shasum"
    else
        # exit early with an error if no hashing binary can be found since it is required later
        exit 1
    fi
fi

# Put file into place if it has changed
if [ ! -f "${FILENAME}" ] || [ "$(${SHA_CMD} <$FILENAME)" != "$(${SHA_CMD} <$FILENAME.new)" ]; then
    mv -f $FILENAME.new $FILENAME
fi
