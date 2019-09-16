#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage Check Point Firewall (c) 2019
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
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: cp_mgmt_package
short_description: Manages package objects on Check Point over Web Services API
description:
  - Manages package objects on Check Point devices including creating, updating and removing objects.
  - All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  name:
    description:
      - Object name.
    type: str
    required: True
  access:
    description:
      - True - enables, False - disables access & NAT policies, empty - nothing is changed.
    type: bool
  desktop_security:
    description:
      - True - enables, False - disables Desktop security policy, empty - nothing is changed.
    type: bool
  installation_targets:
    description:
      - Which Gateways identified by the name or UID to install the policy on.
    type: list
  qos:
    description:
      - True - enables, False - disables QoS policy, empty - nothing is changed.
    type: bool
  qos_policy_type:
    description:
      - QoS policy type.
    type: str
    choices: ['recommended', 'express']
  tags:
    description:
      - Collection of tag identifiers.
    type: list
  threat_prevention:
    description:
      - True - enables, False - disables Threat policy, empty - nothing is changed.
    type: bool
  vpn_traditional_mode:
    description:
      - True - enables, False - disables VPN traditional mode, empty - nothing is changed.
    type: bool
  color:
    description:
      - Color of the object. Should be one of existing colors.
    type: str
    choices: ['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green', 'khaki', 'orchid', 'dark orange', 'dark sea green',
             'pink', 'turquoise', 'dark blue', 'firebrick', 'brown', 'forest green', 'gold', 'dark gold', 'gray', 'dark gray', 'light green', 'lemon chiffon',
             'coral', 'sea green', 'sky blue', 'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange', 'red', 'sienna', 'yellow']
  comments:
    description:
      - Comments string.
    type: str
  details_level:
    description:
      - The level of detail for some of the fields in the response can vary from showing only the UID value of the object to a fully detailed
        representation of the object.
    type: str
    choices: ['uid', 'standard', 'full']
  ignore_warnings:
    description:
      - Apply changes ignoring warnings.
    type: bool
  ignore_errors:
    description:
      - Apply changes ignoring errors. You won't be able to publish such a changes. If ignore-warnings flag was omitted - warnings will also be ignored.
    type: bool
  access_layers:
    description:
      - Access policy layers.
    type: dict
    suboptions:
      add:
        description:
          - Collection of Access layer objects to be added identified by the name or UID.
        type: list
        suboptions:
          name:
            description:
              - Layer name or UID.
            type: str
          position:
            description:
              - Layer position.
            type: int
      remove:
        description:
          - Collection of Access layer objects to be removed identified by the name or UID.
        type: list
      value:
        description:
          - Collection of Access layer objects to be set identified by the name or UID. Replaces existing Access layers.
        type: list
  threat_layers:
    description:
      - Threat policy layers.
    type: dict
    suboptions:
      add:
        description:
          - Collection of Threat layer objects to be added identified by the name or UID.
        type: list
        suboptions:
          name:
            description:
              - Layer name or UID.
            type: str
          position:
            description:
              - Layer position.
            type: int
      remove:
        description:
          - Collection of Threat layer objects to be removed identified by the name or UID.
        type: list
      value:
        description:
          - Collection of Threat layer objects to be set identified by the name or UID. Replaces existing Threat layers.
        type: list
extends_documentation_fragment: checkpoint_objects
"""

EXAMPLES = """
- name: add-package
  cp_mgmt_package:
    access: true
    color: green
    comments: My Comments
    name: New_Standard_Package_1
    state: present
    threat_prevention: false

- name: set-package
  cp_mgmt_package:
    access_layers:
      add:
      - name: New Access Layer 1
        position: 1
    name: Standard
    state: present
    threat_layers:
      add:
      - name: New Layer 1
        position: 2

- name: delete-package
  cp_mgmt_package:
    name: New Standard Package 1
    state: absent
"""

RETURN = """
cp_mgmt_package:
  description: The checkpoint object created or updated.
  returned: always, except when deleting the object.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_objects, api_call


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        access=dict(type='bool'),
        desktop_security=dict(type='bool'),
        installation_targets=dict(type='list'),
        qos=dict(type='bool'),
        qos_policy_type=dict(type='str', choices=['recommended', 'express']),
        tags=dict(type='list'),
        threat_prevention=dict(type='bool'),
        vpn_traditional_mode=dict(type='bool'),
        color=dict(type='str', choices=['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green',
                                        'khaki', 'orchid', 'dark orange', 'dark sea green', 'pink', 'turquoise', 'dark blue', 'firebrick', 'brown',
                                        'forest green', 'gold', 'dark gold', 'gray', 'dark gray', 'light green', 'lemon chiffon', 'coral', 'sea green',
                                        'sky blue', 'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange', 'red', 'sienna',
                                        'yellow']),
        comments=dict(type='str'),
        details_level=dict(type='str', choices=['uid', 'standard', 'full']),
        ignore_warnings=dict(type='bool'),
        ignore_errors=dict(type='bool'),
        access_layers=dict(type='dict', options=dict(
            add=dict(type='list', options=dict(
                name=dict(type='str'),
                position=dict(type='int')
            )),
            remove=dict(type='list'),
            value=dict(type='list')
        )),
        threat_layers=dict(type='dict', options=dict(
            add=dict(type='list', options=dict(
                name=dict(type='str'),
                position=dict(type='int')
            )),
            remove=dict(type='list'),
            value=dict(type='list')
        ))
    )
    argument_spec.update(checkpoint_argument_spec_for_objects)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    api_call_object = 'package'

    result = api_call(module, api_call_object)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
