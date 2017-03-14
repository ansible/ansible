#!/usr/bin/python
#
# Copyright 2016 Red Hat | Ansible
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# This is a windows documentation stub.  Actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: win_path
version_added: "2.3"
short_description: Manage Windows path environment variables
description:
    - Allows element-based ordering, addition, and removal of Windows path environment variables.
options:
  name:
    description:
      - Target path environment variable name
    default: PATH
  elements:
    description:
      - A single path element, or a list of path elements (ie, directories) to add or remove.
      - When multiple elements are included in the list (and C(state) is C(present)), the elements are guaranteed to appear in the same relative order in the resultant path value.
      - Variable expansions (eg, C(%VARNAME%)) are allowed, and are stored unexpanded in the target path element.
      - Any existing path elements not mentioned in C(elements) are always preserved in their current order.
      - New path elements are appended to the path, and existing path elements may be moved closer to the end to satisfy the requested ordering.
      - Paths are compared in a case-insensitive fashion, and trailing backslashes are ignored for comparison purposes. However, note that trailing backslashes in YAML require quotes.
    required: true
  state:
    description:
      - Whether the path elements specified in C(elements) should be present or absent.
    choices:
      - present
      - absent
  scope:
    description:
      - The level at which the environment variable specified by C(name) should be managed (either for the current user or global machine scope).
    choices:
      - machine
      - user
    default: machine
author: "Matt Davis (@nitzmahone)"
notes:
   - This module is for modifying indidvidual elements of path-like
     environment variables. For general-purpose management of other
     environment vars, use the M(win_environment) module.
   - This module does not broadcast change events.
     This means that the minority of windows applications which can have
     their environment changed without restarting will not be notified and
     therefore will need restarting to pick up new environment settings.
     User level environment variables will require an interactive user to
     log out and in again before they become available.
'''

EXAMPLES = r'''
- name: Ensure that system32 and Powershell are present on the global system path, and in the specified order
  win_path:
    elements:
    - '%SystemRoot%\system32'
    - '%SystemRoot%\system32\WindowsPowerShell\v1.0'

- name: Ensure that C:\Program Files\MyJavaThing is not on the current user's CLASSPATH
  win_path:
    name: CLASSPATH
    elements: C:\Program Files\MyJavaThing
    scope: user
    state: absent
'''
