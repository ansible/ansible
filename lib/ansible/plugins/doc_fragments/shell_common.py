# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # common shelldocumentation fragment
    DOCUMENTATION = r'''
options:
  remote_tmp:
    description:
    - Temporary directory to use on targets when executing tasks.
    type: path
    default: '~/.ansible/tmp'
    env: [{name: ANSIBLE_REMOTE_TEMP}, {name: ANSIBLE_REMOTE_TMP}]
    ini:
    - section: defaults
      key: remote_tmp
    vars:
    - name: ansible_remote_tmp
  system_tmpdirs:
    description:
    - List of valid system temporary directories for Ansible to choose when it cannot use
      C(remote_tmp), normally due to permission issues.
    - These must be world readable, writable, and executable.
    type: list
    default: [ /var/tmp, /tmp ]
    env: [{name: ANSIBLE_SYSTEM_TMPDIRS}]
    ini:
    - section: defaults
      key: system_tmpdirs
    vars:
    - name: ansible_system_tmpdirs
  async_dir:
    description:
     - Directory in which ansible will keep async job information.
    type: path
    default: '~/.ansible_async'
    env: [{name: ANSIBLE_ASYNC_DIR}]
    ini:
    - section: defaults
      key: async_dir
    vars:
    - name: ansible_async_dir
  environment:
    description:
    - Dictionary of environment variables and their values to use when executing commands.
    type: dict
    default: {}
  admin_users:
    description:
    - List of users to be expected to have admin privileges.
    - This is used by the controller to determine how to share temporary files between the remote user and the become user.
    type: list
    default: [ root, toor ]
    env:
    - name: ANSIBLE_ADMIN_USERS
    ini:
    - section: defaults
      key: admin_users
    vars:
    - name: ansible_admin_users
'''
