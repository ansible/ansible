#!/usr/bin/env bash

set -eux

# Ensure that when a non-distro 'distro' package is in PYTHONPATH, we fallback
# to our bundled one.
new_pythonpath="$OUTPUT_DIR/pythonpath"
mkdir -p "$new_pythonpath/distro"
touch "$new_pythonpath/distro/__init__.py"

export PYTHONPATH="$new_pythonpath:$PYTHONPATH"

# Sanity test to make sure the above worked
set +e
distro_id_fail="$(python -c 'import distro; distro.id' 2>&1)"
set -e
grep -q "AttributeError:.*has no attribute 'id'" <<< "$distro_id_fail"

# ansible.module_utils.common.sys_info imports distro, and itself gets imported
# in DataLoader, so all we have to do to test the fallback is run `ansible`.
ansirun="$(ansible -i ../../inventory -a "echo \$PYTHONPATH" localhost)"
grep -q "$new_pythonpath" <<< "$ansirun"

rm -rf "$new_pythonpath"
