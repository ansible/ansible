#!/usr/bin/env bash

set -eu

# Create test scenarios at runtime that do not pass sanity tests.
# This avoids the need to create ignore entries for the tests.

(
  cd ansible_collections/ns/col/plugins/modules

  touch no-shebang-executable.py && chmod +x no-shebang-executable.py # file without shebang should not be executable
  python -c "open('utf-32-be-bom.py', 'wb').write(b'\x00\x00\xFE\xFF')" # file starts with a UTF-32 (BE) byte order mark
  python -c "open('utf-32-le-bom.py', 'wb').write(b'\xFF\xFE\x00\x00')" # file starts with a UTF-32 (LE) byte order mark
  python -c "open('utf-16-be-bom.py', 'wb').write(b'\xFE\xFF')" # file starts with a UTF-16 (BE) byte order mark
  python -c "open('utf-16-le-bom.py', 'wb').write(b'\xFF\xFE')" # file starts with a UTF-16 (LE) byte order mark
  python -c "open('utf-8-bom.py', 'wb').write(b'\xEF\xBB\xBF')" # file starts with a UTF-8 byte order mark
  echo '#!/usr/bin/python' > python-executable.py && chmod +x python-executable.py # module should not be executable
  echo '#!invalid' > python-wrong-shebang.py # expected module shebang "b'#!/usr/bin/python'" but found: b'#!invalid'
)

(
  cd ansible_collections/ns/col/scripts

  echo '#!/usr/bin/custom' > unexpected-shebang # unexpected non-module shebang: b'#!/usr/bin/custom'

  echo '#!/usr/bin/make -f' > Makefile && chmod +x Makefile # pass
  echo '#!/bin/bash -eu' > bash_eu.sh && chmod +x bash_eu.sh # pass
  echo '#!/bin/bash -eux' > bash_eux.sh && chmod +x bash_eux.sh # pass
  echo '#!/usr/bin/env fish' > env_fish.fish && chmod +x env_fish.fish # pass
  echo '#!/usr/bin/env pwsh' > env_pwsh.ps1 && chmod +x env_pwsh.ps1 # pass
)

mkdir ansible_collections/ns/col/examples

(
  cd ansible_collections/ns/col/examples

  echo '#!/usr/bin/custom' > unexpected-shebang # pass
)

source ../collection/setup.sh

set -x

ansible-test sanity --test shebang --color --lint --failure-ok "${@}" > actual.txt

diff -u "${TEST_DIR}/expected.txt" actual.txt
