# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # common shelldocumentation fragment
    DOCUMENTATION = """
options:
  remote_tmp:
    description:
      - Temporary directory to use on targets when executing tasks.
    default: '~/.ansible/tmp'
    env: [{name: ANSIBLE_REMOTE_TEMP}, {name: ANSIBLE_REMOTE_TMP}]
    ini:
      - section: defaults
        key: remote_tmp
    vars:
      - name: ansible_remote_tmp
  common_remote_group:
    name: Enables changing the group ownership of temporary files and directories
    default: null
    description:
      - Checked when Ansible needs to execute a module as a different user.
      - If setfacl and chown both fail and do not let the different user access the module's files, they will be chgrp'd to this group.
      - In order for this to work, the remote_user and become_user must share a common group and this setting must be set to that group.
    env: [{name: ANSIBLE_COMMON_REMOTE_GROUP}]
    vars:
      - name: ansible_common_remote_group
    ini:
    - {key: common_remote_group, section: defaults}
    version_added: "2.10"
  system_tmpdirs:
    description:
       - "List of valid system temporary directories on the managed machine for Ansible to validate
         C(remote_tmp) against, when specific permissions are needed.  These must be world
         readable, writable, and executable. This list should only contain directories which the
         system administrator has pre-created with the proper ownership and permissions otherwise
         security issues can arise."
       - When C(remote_tmp) is required to be a system temp dir and it does not match any in the list,
         the first one from the list will be used instead.
    default: [ /var/tmp, /tmp ]
    type: list
    elements: string
    env: [{name: ANSIBLE_SYSTEM_TMPDIRS}]
    ini:
      - section: defaults
        key: system_tmpdirs
    vars:
      - name: ansible_system_tmpdirs
  async_dir:
    description:
       - Directory in which ansible will keep async job information
    default: '~/.ansible_async'
    env: [{name: ANSIBLE_ASYNC_DIR}]
    ini:
      - section: defaults
        key: async_dir
    vars:
      - name: ansible_async_dir
  environment:
    type: list
    elements: dictionary
    default: [{}]
    description:
      - List of dictionaries of environment variables and their values to use when executing commands.
    keyword:
      - name: environment
  admin_users:
    type: list
    elements: string
    default: ['root', 'toor']
    description:
      - list of users to be expected to have admin privileges. This is used by the controller to
        determine how to share temporary files between the remote user and the become user.
    env:
      - name: ANSIBLE_ADMIN_USERS
    ini:
      - section: defaults
        key: admin_users
    vars:
      - name: ansible_admin_users
  world_readable_temp:
    version_added: '2.10'
    default: False
    description:
      - This makes the temporary files created on the machine world-readable and will issue a warning instead of failing the task.
      - It is useful when becoming an unprivileged user.
    env:
      - name: ANSIBLE_SHELL_ALLOW_WORLD_READABLE_TEMP
    vars:
      - name: ansible_shell_allow_world_readable_temp
    ini:
    - {key: allow_world_readable_tmpfiles, section: defaults}
    type: boolean
"""
