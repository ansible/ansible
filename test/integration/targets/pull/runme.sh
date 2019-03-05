#!/usr/bin/env bash

set -eux
set -o pipefail

# http://unix.stackexchange.com/questions/30091/fix-or-alternative-for-mktemp-in-os-x
temp_dir=$(shell mktemp -d 2>/dev/null || mktemp -d -t 'ansible-testing-XXXXXXXXXX')
trap 'rm -rf "${temp_dir}"' EXIT

pull_dir="${temp_dir}/pull"
# Remote repository for running ansible-pull against localhost only with fake role that has recursive submodules
remote_repo='https://github.com/ju2wheels/test_ansible_pull.git'
repo_dir="${temp_dir}/repo"
temp_log="${temp_dir}/pull.log"

ansible-playbook setup.yml

cleanup="$(pwd)/cleanup.yml"

trap 'ansible-playbook "${cleanup}"' EXIT

cp -av "pull-integration-test" "${repo_dir}"
cd "${repo_dir}"
(
  git init
  git config user.email "ansible@ansible.com"
  git config user.name  "Ansible Test Runner"
  git add .
  git commit -m "Initial commit."
)

function git_supports_depth()
{
  # Output boolean 1 for true if git supports --depth or 0 for false

  if [[ -z "$(git clone -h | grep '\--depth')" ]]; then
    echo -n '0'
  else
    echo -n '1'
  fi

  return 0
}

function localhost_only
{
  local ansible_output_log=''

  if [[ $# -ne 1 ]]; then
    echo 'Usage: localhost_only <ansible_output_log>' 1>&2

    return 1
  fi

  ansible_output_log="$1"

  # test for https://github.com/ansible/ansible/issues/13681
  if egrep '127\.0\.0\.1.*ok=' < "${ansible_output_log}"; then
    echo "Found host 127.0.0.1 in output. Only localhost should be present." 1>&2

    return 1
  fi

  return 0
}

function localhost_ran
{
  local ansible_output_log=''

  if [[ $# -ne 1 ]]; then
    echo 'Usage: localhost_ran <ansible_output_log>' 1>&2

    return 1
  fi

  ansible_output_log="$1"

  # make sure one host was run
  if ! egrep 'localhost.*ok=' < "${ansible_output_log}"; then
    echo "Did not find host localhost in output." 1>&2

    return 1
  fi

  return 0
}

function magickeyword_in_output
{
  local ansible_output_log=''

  if [[ $# -ne 1 ]]; then
    echo 'Usage: magickeyword_in_output <ansible_output_log>' 1>&2

    return 1
  fi

  ansible_output_log="$1"

  # test for https://github.com/ansible/ansible/issues/13688
  if ! grep MAGICKEYWORD < "${ansible_output_log}"; then
    echo "Missing MAGICKEYWORD in output." 1>&2

    return 1
  fi

  return 0
}

function main_repo_at_tag
{
  local current_tag=''
  local tag=''

  if [[ $# -ne 1 ]]; then
    echo 'Usage: main_repo_at_tag <tag>' 1>&2

    return 1
  fi

  tag="$1"

  pushd "${pull_dir}"

  set +x

  current_tag="$(git describe --tags)"

  set -x

  if [[ "${current_tag}" != "${tag}" ]]; then
    echo "Main ansible-pull repo was not checked out to tag ${tag}" 1>&2

    return 1
  fi

  popd

  return 0
}

function main_repo_full_cloned()
{
  pushd "${pull_dir}"

  if [[ "$(git log --oneline | wc -l)" -eq 1 ]]; then
    echo "Main ansible-pull repo was not full cloned by git" 1>&2

    return 1
  fi

  popd

  return 0
}

function main_repo_shallow_cloned
{
  local ansible_output_log=''

  if [[ $# -ne 1 ]]; then
    echo 'Usage: main_repo_shallow_cloned <ansible_output_log>' 1>&2

    return 1
  fi

  ansible_output_log="$1"

  if [[ "$(git_supports_depth)" -eq 0 ]]; then
    main_repo_full_cloned

    return $?
  else
    pushd "${pull_dir}"

    if [[ "$(git log --oneline | wc -l)" -gt 1 ]]; then
      echo "Main ansible-pull repo was not shallow cloned by git" 1>&2

      return 1
    fi

    popd
  fi

  return 0
}

function submodule_initialized()
{
  pushd "${pull_dir}"

  if [[ -z "$(ls roles/test_submodules/)" ]]; then
    echo "Primary submodule for role test_submodules was not initialized" 1>&2

    return 1
  fi

  popd
}

function submodule_recursively_initialized()
{
  pushd "${pull_dir}"

  if ! [[ -d "roles/test_submodules/submodule1/submodule2" ]]; then
    echo "Recursive submodules for role test_submodules were not initialized" 1>&2

    return 1
  fi

  popd

  return 0
}

function submodule_full_cloned()
{
  pushd "${pull_dir}/roles/test_submodules"

  if [[ "$(git log --oneline | wc -l)" -eq 1 ]]; then
    echo "Primary submodule for role test_submodules was not full cloned by git" 1>&2

    return 1
  fi

  popd

  return 0
}

function submodule_shallow_cloned
{
  local ansible_output_log=''

  if [[ $# -ne 1 ]]; then
    echo 'Usage: main_repo_shallow_cloned <ansible_output_log>' 1>&2

    return 1
  fi

  ansible_output_log="$1"

  if [[ "$(git_supports_depth)" -eq 0 ]]; then
    submodule_full_cloned

    return $?
  else
    pushd "${pull_dir}/roles/test_submodules"

    if [[ "$(git log --oneline | wc -l)" -gt 1 ]]; then
      echo "Primary submodule for role test_submodules was not shallow cloned by git" 1>&2

      return 1
    fi

    popd
  fi

  return 0
}

ANSIBLE_CONFIG='' ansible-pull -d "${pull_dir}" -U "${repo_dir}" "$@" | tee "${temp_log}"

localhost_only "${temp_log}"
localhost_ran "${temp_log}"
magickeyword_in_output "${temp_log}"

rm -rf "${pull_dir}"

# ensure complex extra vars work
PASSWORD='test'
USER=${USER:-'broken_docker'}
JSON_EXTRA_ARGS='{"docker_registries_login": [{ "docker_password": "'"${PASSWORD}"'", "docker_username": "'"${USER}"'", "docker_registry_url":"repository-manager.company.com:5001"}], "docker_registries_logout": [{ "docker_password": "'"${PASSWORD}"'", "docker_username": "'"${USER}"'", "docker_registry_url":"repository-manager.company.com:5001"}] }'

ANSIBLE_CONFIG='' ansible-pull -d "${pull_dir}" -U "${repo_dir}" -e "${JSON_EXTRA_ARGS}" "$@" --tags untagged,test_ev | tee "${temp_log}"

localhost_only "${temp_log}"
localhost_ran "${temp_log}"
magickeyword_in_output "${temp_log}"

rm -rf "${pull_dir}"

# Run ansible-pull with defaults (which is shallow clone on main repository and recursive full clone on submodules) and accept GH host key
ANSIBLE_CONFIG='' ansible-pull -d "${pull_dir}" -U "${remote_repo}" --accept-host-key "$@" | tee "${temp_log}"

main_repo_shallow_cloned "${temp_log}"
submodule_initialized
submodule_recursively_initialized
submodule_full_cloned

rm -rf "${pull_dir}"

# Run ansible-pull with --full for full clone and accept GH host key
ANSIBLE_CONFIG='' ansible-pull -d "${pull_dir}" -U "${remote_repo}" --accept-host-key --full "$@" | tee "${temp_log}"

main_repo_full_cloned
submodule_initialized
submodule_recursively_initialized
submodule_full_cloned

rm -rf "${pull_dir}"

# Run ansible-pull with --checkout at tag 1.0.0 and accept GH host key
ANSIBLE_CONFIG='' ansible-pull -d "${pull_dir}" -U "${remote_repo}" --accept-host-key --checkout '1.0.0' "$@" | tee "${temp_log}"

main_repo_at_tag '1.0.0'
main_repo_shallow_cloned "${temp_log}"
submodule_initialized
submodule_recursively_initialized
submodule_full_cloned

rm -rf "${pull_dir}"

# Run ansible-pull with depth of 1 and accept GH host key using --module-args
ANSIBLE_CONFIG='' ansible-pull -d "${pull_dir}" -U "${remote_repo}" --module-args 'accept_hostkey=yes depth=1' "$@" | tee "${temp_log}"

main_repo_shallow_cloned "${temp_log}"
submodule_initialized
submodule_recursively_initialized
submodule_full_cloned

rm -rf "${pull_dir}"

# Run ansbible-pull with --module-args and no depth to emulate --full and accept GH host key using --module-args
ANSIBLE_CONFIG='' ansible-pull -d "${pull_dir}" -U "${remote_repo}" --module-args 'accept_hostkey=yes' "$@" | tee "${temp_log}"

main_repo_full_cloned
submodule_initialized
submodule_recursively_initialized
submodule_full_cloned

rm -rf "${pull_dir}"

# Run ansible-pull with checkout at tag 1.0.0 and accept GH host key using --module-args
ANSIBLE_CONFIG='' ansible-pull -d "${pull_dir}" -U "${remote_repo}" --module-args 'accept_hostkey=yes depth=1 version=1.0.0' "$@" | tee "${temp_log}"

main_repo_at_tag '1.0.0'
main_repo_shallow_cloned "${temp_log}"
submodule_initialized
submodule_recursively_initialized
submodule_full_cloned

rm -rf "${pull_dir}"
