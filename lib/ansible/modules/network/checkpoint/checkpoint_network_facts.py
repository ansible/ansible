#!/usr/bin/python
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
#

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: checkpoint_host
short_description: Manages host objects on Checkpoint over Web Services API
description:
  - Manages host objects on Checkpoint devices including creating, updating, removing access rules objects.
    All operations are performed over Web Services API.
version_added: "2.8"
author: "Ansible by Red Hat (@rcarrillocruz)"
options:
  name:
    description:
      - Name of the access rule.
    type: str
    required: True
  ip_address:
    description:
      - IP address of the host object.
    type: str
  state:
    description:
      - State of the access rule (present or absent). Defaults to present.
    type: str
    default: present
  auto_publish_session:
    description:
      - Publish the current session if changes have been performed
        after task completes.
    type: bool
    default: 'yes'
  auto_install_policy:
    description:
      - Install the package policy if changes have been performed
        after the task completes.
    type: bool
    default: 'yes'
  policy_package:
    description:
      - Package policy name to be installed.
    type: bool
    default: 'standard'
  targets:
    description:
      - Targets to install the package policy on.
    type: list
"""

EXAMPLES = """
- name: Create host object
  checkpoint_host:
    name: attacker
    ip_address: 192.168.0.15

- name: Delete host object
  checkpoint_host:
    name: attacker
    state: absent
"""

RETURN = """
checkpoint_hosts:
  description: The checkpoint host object created or updated.
  returned: always, except when deleting the host.
  type: list
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec, api_call_facts
import ntpath


def main():
    argument_spec = dict(
        name=dict(type='str'),
        uid=dict(type='str'),
        details_level=dict(type='str')
    )
    argument_spec.update(checkpoint_argument_spec)
    required_one_of = [['name', 'uid']]
    mutually_exclusive = [['name', 'uid']]
    module = AnsibleModule(argument_spec=argument_spec, required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive)
    #file_name = ntpath.basename(__file__).split(".")[0]
    #api_call_object = file_name.split("_", 1)[-1].replace("_", "-")
    api_call_object = "network"

    payload = {'name': module.params['name'],
               'uid': module.params['uid']}

    api_call_facts(module, api_call_object, payload)


if __name__ == '__main__':
    main()
