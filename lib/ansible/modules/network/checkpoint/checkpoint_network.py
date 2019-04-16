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
module: checkpoint_network
short_description: Manages network objects on Checkpoint over Web Services API
description:
  - Manages network objects on Checkpoint devices including creating, updating, removing network objects.
    All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  name:
    description:
      - Object name. Should be unique in the domain.
    type: str
  uid:
    description:
      Object unique identifier.
    type: str
  subnet:
    description:
      - IPv4 or IPv6 network address. If both addresses are required use subnet4 and subnet6 fields explicitly.
    type: str
  subnet4:
    description:
      - IPv4 network address.
    type: str
  subnet6:
    description:
      - IPv6 network address.
    type: str
  mask_length:
    description:
      - IPv4 or IPv6 network mask length. If both masks are required use mask-length4 and mask-length6 fields
        explicitly. Instead of IPv4 mask length it is possible to specify IPv4 mask itself in subnet-mask field.
    type: int
  mask_length4:
    description:
      - IPv4 network mask length.
    type: int
  mask_length6:
    description:
      - IPv6 network mask length.
    type: int
  subnet_mask:
    description:
      - IPv4 network mask.
    type: str
  nat_settings:
    description:
      - NAT settings.
    type: dict
  tags:
    description:
      - Collection of tag identifiers.
    type: list
  broadcast:
    description:
      - Allow broadcast address inclusion.
    type: str
    choices: ['disallow', 'allow']
  set_if_exists:
    description:
      - If another object with the same identifier already exists, it will be updated. The command behaviour will be the
        same as if originally a set command was called. Pay attention that original object's fields will be overwritten
        by the fields provided in the request payload!
    type: bool
  color:
    description:
      - Color of the object. Should be one of existing colors.
    type: str
    choices: ['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green', 'khaki', 'orchid',
              'dark orange', 'dark sea green', 'pink', 'turquoise', 'dark blue', 'firebrick', 'brown', 'forest green',
              'gold', 'dark gold', 'gray', 'dark gray', 'light green', 'lemon chiffon', 'coral', 'sea green',
              'sky blue', 'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange', 'red',
              'sienna', 'yellow']
  comments:
    description:
      - Comments string.
    type: str
  details_level:
    description:
      - The level of detail for some of the fields in the response can vary from showing only the UID value of the
        object to a fully detailed representation of the object.
    type: str
    choices: ['uid', 'standard', 'full']
  groups:
    description:
      - Collection of group identifiers.
    type: list
  ignore_warnings:
    description:
      - Apply changes ignoring warnings.
    type: bool
  ignore_errors:
    description:
      - Apply changes ignoring errors. You won't be able to publish such a changes. If ignore-warnings flag was omitted
        - warnings will also be ignored.
    type: bool
  state:
    description:
      - State of the access rule (present or absent). Defaults to present.
    type: str
    required: True
  auto_publish_session:
    description:
      - Publish the current session if changes have been performed
        after task completes.
    type: bool
  auto_install_policy:
    description:
      - Install the package policy if changes have been performed
        after the task completes.
    type: bool
  policy_package:
    description:
      - Package policy name to be installed.
    type: str
  targets:
    description:
      - Targets to install the package policy on.
    type: list
"""

EXAMPLES = """
- name: Add network object
  checkpoint_host:
    name: "New Network 1"
    subnet: "192.0.2.0"
    subnet_mask : "255.255.255.0"


- name: Delete network object
  checkpoint_host:
    name: "New Network 1"
    state: absent
"""

RETURN = """
checkpoint_networks:
  description: The checkpoint network object created or updated.
  returned: always, except when deleting the network.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec, api_call


def main():
    argument_spec = dict(
        name=dict(type='str'),
        uid=dict(type='str'),
        subnet=dict(type='str'),
        subnet4=dict(type='str'),
        subnet6=dict(type='str'),
        mask_length=dict(type='int'),
        mask_length4=dict(type='int'),
        mask_length6=dict(type='int'),
        subnet_mask=dict(type='str'),
        nat_settings=dict(type='dict'),
        tags=dict(type='list'),
        broadcast=dict(type='str', choices=['disallow', 'allow']),
        set_if_exists=dict(type='bool'),
        color=dict(type='str', choices=['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green',
                                        'khaki', 'orchid', 'dark orange', 'dark sea green', 'pink', 'turquoise',
                                        'dark blue', 'firebrick', 'brown', 'forest green', 'gold', 'dark gold', 'gray',
                                        'dark gray', 'light green', 'lemon chiffon', 'coral', 'sea green', 'sky blue',
                                        'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange',
                                        'red', 'sienna', 'yellow']),
        comments=dict(type='str'),
        details_level=dict(type='str', choices=['uid', 'standard', 'full']),
        groups=dict(type='list'),
        ignore_warnings=dict(type='bool'),
        ignore_errors=dict(type='bool'),
        state=dict(type='str', required=True)
    )

    user_parameters = list(argument_spec.keys())
    user_parameters.remove('state')
    argument_spec.update(checkpoint_argument_spec)
    module = AnsibleModule(argument_spec=argument_spec, required_one_of=[['name', 'uid']],
                           mutually_exclusive=[['name', 'uid']])
    api_call_object = "network"

    unique_payload_for_get = {'name': module.params['name']} if module.params['name'] else {'uid': module.params['uid']}

    api_call(module, api_call_object, user_parameters, unique_payload_for_get)


if __name__ == '__main__':
    main()
