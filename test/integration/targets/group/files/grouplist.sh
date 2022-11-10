#!/usr/bin/env bash

#- name: make a list of groups
#  shell: |
#      cat /etc/group | cut -d: -f1
#  register: group_names
#  when: 'ansible_distribution != "MacOSX"'

#- name: make a list of groups [mac]
#  shell: dscl localhost -list /Local/Default/Groups
#  register: group_names
#  when: 'ansible_distribution == "MacOSX"'

DISTRO="$1"
PREFIX_PATH="$2"

if [[ "${DISTRO}" == "MacOSX" ]]; then
    dscl localhost -list /Local/Default/Groups
else
    GROUPFILE="/etc/group"
    if [[ -n "${PREFIX_PATH}" ]]; then
        GROUPFILE="${PREFIX_PATH}${GROUPFILE}"
    fi
    grep -E -v ^\# "${GROUPFILE}" | cut -d: -f1
fi
