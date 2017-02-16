#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ansible module to launch the reset_ssh_session action plugin

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Ansible is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
"""

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: reset_ssh_session
version_added: "2.2"
short_description: Remove the CP handle file forcing Ansible to reconnect on next task
author: "Dan Hirsch (@hackndoes)"
options:
  control_persist_path:
    description:
      - Sets the path to the ControlPersist handle file if it was set in ansible configuration
      - Leave empty if using the default ansible configuration
    choices:
      - None/Undefined
      - String of Path to location of the file as configuration in ansible.cfg
    default:
      - <ansible_user_dir>/.ansible/cp/ansible-ssh-<inventory_hostname>-22-<ansible_user_id>
'''

EXAMPLES = '''
- name: Reset the ssh connection with default configuration
  reset_ssh_connection:

#ansible.cfg configuration
[ssh_connection]
control_path = "/tmp/my-file-%%r-%%h-22"

- name: Reset the ssh connection with this configured ansible.cfg
  reset_ssh_connection:
    control_persist_path: "<ansible_user_dir>/.ansible/cp/ansible-ssh-<inventory_hostname>-22-<ansible_user_id>"
'''

RETURN = '''
changed:
  description: Specifies wether the control_persist_path points to a file and had it removed
  returned: always
  type: bool
  sample: False
'''

def main():
    pass

if __name__ == "__main__":
    main()
