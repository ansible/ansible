#!/usr/bin/env bash
# Verify change detection handles untracked paths which cannot be read as files.

set -eux -o pipefail

# ansible-test only runs within a content root, and inside the ansible source tree change
# detection resolves git against the ansible repository, so work outside it.
tmp_dir=$(mktemp -d)

trap 'rm -rf "${tmp_dir}"' EXIT

log="${tmp_dir}/sanity.log"

mkdir -p "${tmp_dir}/ansible_collections/ns/col"
cd "${tmp_dir}/ansible_collections/ns/col"

git init --quiet --initial-branch main .
git config user.name 'Ansible Test'
git config user.email 'ansible-test@ansible.com'
echo content > README.md
git add README.md
git commit --quiet --message 'Initial commit.'
git checkout --quiet -b feature

# git reports each of these as a single entry instead of recursing into it
mkdir real-directory
ln -s real-directory symlink-to-directory
ln -s does-not-exist broken-symlink
git init --quiet nested-repository
touch nested-repository/content.txt
echo content > regular-file  # control

# Reading any of these as a file raises, which exits non-zero and trips `set -e`.
ansible-test sanity --test pep8 --changed --base-branch main -v 2>&1 | tee "${log}"

# Verbose output lists each detected path, so these also fail if one was skipped.
grep -qF 'symlink-to-directory' "${log}"
grep -qF 'broken-symlink' "${log}"
grep -qF 'nested-repository/' "${log}"
grep -qF 'regular-file' "${log}"
