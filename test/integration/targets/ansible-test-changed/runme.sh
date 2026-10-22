#!/usr/bin/env bash
# Verify change detection handles untracked paths which cannot be read as files.

set -eux -o pipefail

# tests must be executed outside of the ansible source tree
tmp_dir=$(mktemp -d)

trap 'rm -rf "${tmp_dir}"' EXIT

TEST_DIR="$PWD"

# Each scenario creates an untracked path named "changed-path" which git reports as a single entry
# instead of recursing into it.

symlink-to-directory() {
  mkdir target
  ln -s target changed-path
}

broken-symlink() {
  ln -s does-not-exist changed-path
}

nested-repository() {
  git init --quiet changed-path
  touch changed-path/content.txt
}

regular-file() {
  echo content > changed-path  # control scenario
}

run_scenario() {
  local scenario="$1"
  local work_dir="${tmp_dir}/${scenario}"
  local log="${tmp_dir}/${scenario}.log"

  mkdir "${work_dir}"
  cp -a "${TEST_DIR}/ansible_collections" "${work_dir}"
  cd "${work_dir}/ansible_collections/ns/col"

  git init --quiet --initial-branch main .
  git config user.name 'Ansible Test'
  git config user.email 'ansible-test@ansible.com'
  git add .
  git commit --quiet --message 'Initial commit.'
  git checkout --quiet -b feature

  "${scenario}"

  # Failure to read the path raises, which exits non-zero and trips `set -e`.
  # The timeout only bounds a hang, it is not the test signal.
  timeout 600 ansible-test sanity --test pep8 --changed --untracked --base-branch main -v >"${log}" 2>&1

  # Verbose output lists each detected path, so this also fails if change detection skipped it.
  grep --quiet --fixed-strings 'changed-path' "${log}"

  cd "${TEST_DIR}"
  rm -rf "${work_dir}" "${log}"
}

# Not `run_scenario ... || ...`, which would disable `set -e` for the duration of the call.
for scenario in symlink-to-directory broken-symlink nested-repository regular-file; do
  echo ""
  echo "SCENARIO: ${scenario}: STARTING"
  run_scenario "${scenario}"
  echo "SCENARIO: ${scenario}: PASSED"
done
