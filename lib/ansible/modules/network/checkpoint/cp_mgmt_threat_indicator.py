#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage CheckPoint Firewall (c) 2019
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
module: cp_mgmt_threat_indicator
short_description: Manages threat-indicator objects on Checkpoint over Web Services API
description:
  - Manages threat-indicator objects on Checkpoint devices including creating, updating and removing objects.
    All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  name:
    description:
      - Object name.
    type: str
    required: True
  observables:
    description:
      - The indicator's observables.
    type: list
  observables_raw_data:
    description:
      - The contents of a file containing the indicator's observables.
    type: str
  action:
    description:
      - The indicator's action.
    type: str
    choices: ['Inactive', 'Ask', 'Prevent', 'Detect']
  profile_overrides:
    description:
      - Profiles in which to override the indicator's default action.
    type: list
  tags:
    description:
      - Collection of tag identifiers.
    type: list
    suboptions:
    
  color:
    description:
      - Color of the object. Should be one of existing colors.
    type: str
    choices: ['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green', 'khaki',
             'orchid', 'dark orange', 'dark sea green', 'pink', 'turquoise', 'dark blue', 'firebrick', 'brown',
             'forest green', 'gold', 'dark gold', 'gray', 'dark gray', 'light green', 'lemon chiffon', 'coral',
             'sea green', 'sky blue', 'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange',
             'red', 'sienna', 'yellow']
  comments:
    description:
      - Comments string.
    type: str
  details_level:
    description:
      - The level of detail for some of the fields in the response can vary from showing only the UID value of
        the object to a fully detailed representation of the object.
    type: str
    choices: ['uid', 'standard', 'full']
  ignore_warnings:
    description:
      - Apply changes ignoring warnings.
    type: bool
  ignore_errors:
    description:
      - Apply changes ignoring errors. You won't be able to publish such a changes. If ignore-warnings flag was
        omitted - warnings will also be ignored.
    type: bool
extends_documentation_fragment: checkpoint_objects
"""

EXAMPLES = """
- name: add-threat-indicator
  cp_mgmt_threat_indicator:
    action: ask
    ignore_warnings: true
    name: My_Indicator
    observables:
    _ confidence: medium
      mail_to: someone@somewhere.com
      name: My_Observable
      product: AV
      severity: low
    profile_overrides:
    _ action: detect
      profile: My_Profile

- name: set-threat-indicator
  cp_mgmt_threat_indicator:
    action: prevent
    ignore_warnings: true
    name: My_Indicator
    profile_overrides:
      remove: My_Profile

- name: delete-threat-indicator
  cp_mgmt_threat_indicator:
    name: My_Indicator
    state: absent
"""

RETURN = """
cp_mgmt_threat_indicator:
  description: The checkpoint object created or updated.
  returned: always, except when deleting the object.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_objects, api_call


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        observables=dict(type='list'),
        observables_raw_data=dict(type='str'),
        action=dict(type='str', choices=['Inactive', 'Ask', 'Prevent', 'Detect']),
        profile_overrides=dict(type='list'),
        tags=dict(type='list', options=dict(
        )),
        color=dict(type='str', choices=['aquamarine', 'black', 'blue',
                                        'crete blue', 'burlywood', 'cyan', 'dark green', 'khaki', 'orchid',
                                        'dark orange', 'dark sea green', 'pink', 'turquoise', 'dark blue', 'firebrick',
                                        'brown', 'forest green', 'gold', 'dark gold', 'gray', 'dark gray',
                                        'light green', 'lemon chiffon', 'coral', 'sea green', 'sky blue', 'magenta',
                                        'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange', 'red',
                                        'sienna', 'yellow']),
        comments=dict(type='str'),
        details_level=dict(type='str', choices=['uid', 'standard', 'full']),
        ignore_warnings=dict(type='bool'),
        ignore_errors=dict(type='bool')
    )
    argument_spec.update(checkpoint_argument_spec_for_objects)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    api_call_object = 'threat-indicator'

    result = api_call(module, api_call_object)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
