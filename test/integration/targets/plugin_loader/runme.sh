#!/usr/bin/env bash

set -eux

cleanup() {
    unlink normal/library/_symlink.py

    rm "$core_module_path/modules/deprecated_core_module.py"
    rm "$core_module_path/plugins/connection/deprecated_core_connection.py"
}

pushd normal/library
ln -s _underscore.py _symlink.py
popd

# inject a couple of phony deprecated core plugins
core_module_path=$(dirname "$(python -c 'from importlib.util import find_spec; print(find_spec("ansible").origin)')")

cp deprecated_core_plugins/deprecated_core_module.py "$core_module_path/modules"
cp deprecated_core_plugins/deprecated_core_connection.py "$core_module_path/plugins/connection"

trap 'cleanup' EXIT


# check normal execution
for myplay in normal/*.yml
do
	ansible-playbook "${myplay}" -i ../../inventory -vvv "$@"
	if test $? != 0 ; then
		echo "### Failed to run ${myplay} normally"
		exit 1
	fi
done

# check overrides
for myplay in override/*.yml
do
	ansible-playbook "${myplay}" -i ../../inventory -vvv "$@"
	if test $? != 0 ; then
		echo "### Failed to run ${myplay} override"
		exit 1
	fi
done

# test config loading
ansible-playbook use_coll_name.yml -i ../../inventory -e 'ansible_connection=ansible.builtin.ssh' "$@"

# test filter loading ignoring duplicate file basename
ansible-playbook file_collision/play.yml "$@"

# validate warnings from deprecated core plugins
unset ANSIBLE_DEPRECATION_WARNINGS
ansible-playbook deprecated_core_plugins.yml
