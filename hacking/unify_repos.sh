#!/bin/sh

set -x
set -e
set -u

# get current stuff
git clone git@github.com:ansible/ansible.git ansible_unified
cd ansible_unified/
git submodule init
git submodule update

# add submodules as remotes
git remote add core_modules git@github.com:ansible/ansible-modules-core.git
git remote add extras_modules git@github.com:ansible/ansible-modules-extras.git
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
