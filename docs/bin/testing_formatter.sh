#!/bin/bash -eu

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

# Put file into place if it has changed
if [ "$(sha1sum <$FILENAME)" != "$(sha1sum <$FILENAME.new)" ]; then
    mv -f $FILENAME.new $FILENAME
fi
