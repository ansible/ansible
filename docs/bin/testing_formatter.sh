#!/bin/bash -eu

cat <<- EOF > ../docsite/rst/dev_guide/testing/sanity/index.rst
Sanity Tests
============

The following sanity tests are available as \`\`--test\`\` options for \`\`ansible-test sanity\`\`.
This list is also available using \`\`ansible-test sanity --list-tests\`\`.

.. toctree::
   :maxdepth: 1

$(for test in $(../../test/runner/ansible-test sanity --list-tests); do echo "   ${test}"; done)


EOF
