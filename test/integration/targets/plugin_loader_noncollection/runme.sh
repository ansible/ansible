#!/usr/bin/env bash

set -eux

for plugin_dir in \
    adjacent/library \
    adjacent/filter_plugins \
    module_path \
    configured \
    playbook_dir_only/library
do
    test ! -e "${plugin_dir}/__init__.py"
done

ansible-playbook adjacent/play.yml -i ../../inventory "$@"

set +e
missing_mp="$(ansible-playbook plays/module_path.yml -i ../../inventory "$@" 2>&1)"
mp_status=$?
set -e
if test "${mp_status}" -eq 0; then
    printf '%s\n' "${missing_mp}" >&2
    echo "mp_mod resolved without --module-path" >&2
    exit 1
fi
printf '%s\n' "${missing_mp}"
grep -F 'mp_mod' <<< "${missing_mp}"

ansible-playbook plays/module_path.yml -i ../../inventory -M "${PWD}/module_path" "$@"

set +e
missing_pb="$(ansible testhost -i ../../inventory -m pbdir_mod -c local "$@" 2>&1)"
pb_status=$?
set -e
if test "${pb_status}" -eq 0; then
    printf '%s\n' "${missing_pb}" >&2
    echo "pbdir_mod resolved without --playbook-dir" >&2
    exit 1
fi
printf '%s\n' "${missing_pb}"
grep -F 'pbdir_mod' <<< "${missing_pb}"

pb_out="$(ansible testhost -i ../../inventory -m pbdir_mod --playbook-dir "${PWD}/playbook_dir_only" -c local "$@")"
printf '%s\n' "${pb_out}"
grep -F '"source": "playbook_dir"' <<< "${pb_out}"

set +e
missing_cfg="$(env -u ANSIBLE_LIBRARY ansible-playbook plays/configured.yml -i ../../inventory "$@" 2>&1)"
cfg_status=$?
set -e
if test "${cfg_status}" -eq 0; then
    printf '%s\n' "${missing_cfg}" >&2
    echo "cfg_mod resolved without ANSIBLE_LIBRARY" >&2
    exit 1
fi
printf '%s\n' "${missing_cfg}"
grep -F 'cfg_mod' <<< "${missing_cfg}"

ANSIBLE_LIBRARY="${PWD}/configured" ansible-playbook plays/configured.yml -i ../../inventory "$@"
