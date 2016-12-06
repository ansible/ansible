#!/bin/bash

set -x
set -e
set -u

# get current stuff
git clone https://github.com/ansible/ansible.git ansible_unified
cd ansible_unified/
git submodule init
git submodule update
git remote add upstream git@github.com:ansible/ansible.git

# add submodules as remotes
git remote add core_modules https://github.com/ansible/ansible-modules-core.git
git remote add extras_modules https://github.com/ansible/ansible-modules-extras.git
git fetch --all

# remove submodules
echo "" > .gitmodules
git add .gitmodules
git rm --cached lib/ansible/modules/core/
git rm --cached lib/ansible/modules/extras/
git commit -am "removed core and extras submodules"
rm -rf lib/ansible/modules/core
rm -rf lib/ansible/modules/extras

# merge remotes into old submodule dirs
## core
git merge -s ours --allow-unrelated-histories --no-commit core_modules/devel
git read-tree --prefix=lib/ansible/modules/core -u core_modules/devel
git commit -am 'core modules back to main repo'
## extras
git merge -s ours --allow-unrelated-histories --no-commit extras_modules/devel
git read-tree --prefix=lib/ansible/modules/extras -u extras_modules/devel
git commit -am 'extras modules back to main repo'

for subdir in core extras
do
	# unify directories
	for mydir in $(find lib/ansible/modules/${subdir} -type d)
	do
		mkdir -p ${mydir/$subdir\//}
	done

	# move plugins
	for myfile in $(find lib/ansible/modules/${subdir} -type f)
	do
		if [ -e ${myfile/$subdir\///} ]; then #mostly to avoid __init__.py clobering
			echo "skipping ${myfile} as it already exists in destination"
		else
			git mv ${myfile} ${myfile/$subdir\//}
		fi
	done

	rm -rf lib/ansible/modules/${subdir}
done
