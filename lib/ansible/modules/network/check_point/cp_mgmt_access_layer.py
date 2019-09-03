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
module: cp_mgmt_access_layer
short_description: Manages access-layer objects on Check Point over Web Services API
description:
  - Manages access-layer objects on Check Point devices including creating, updating and removing objects.
  - All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  name:
    description:
      - Object name.
    type: str
    required: True
  add_default_rule:
    description:
      - Indicates whether to include a cleanup rule in the new layer.
    type: bool
  applications_and_url_filtering:
    description:
      - Whether to enable Applications & URL Filtering blade on the layer.
    type: bool
  content_awareness:
    description:
      - Whether to enable Content Awareness blade on the layer.
    type: bool
  detect_using_x_forward_for:
    description:
      - Whether to use X-Forward-For HTTP header, which is added by the  proxy server to keep track of the original source IP.
    type: bool
  firewall:
    description:
      - Whether to enable Firewall blade on the layer.
    type: bool
  implicit_cleanup_action:
    description:
      - The default "catch-all" action for traffic that does not match any explicit or implied rules in the layer.
    type: str
    choices: ['drop', 'accept']
  mobile_access:
    description:
      - Whether to enable Mobile Access blade on the layer.
    type: bool
  shared:
    description:
      - Whether this layer is shared.
    type: bool
  tags:
    description:
      - Collection of tag identifiers.
    type: list
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
extends_documentation_fragment: checkpoint_objects
"""

EXAMPLES = """
- name: add-access-layer
  cp_mgmt_access_layer:
    name: New Layer 1
    state: present

- name: set-access-layer
  cp_mgmt_access_layer:
    applications_and_url_filtering: false
    data_awareness: true
    name: New Layer 1
    state: present

- name: delete-access-layer
  cp_mgmt_access_layer:
    name: New Layer 2
    state: absent
"""

RETURN = """
cp_mgmt_access_layer:
  description: The checkpoint object created or updated.
  returned: always, except when deleting the object.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_objects, api_call


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        add_default_rule=dict(type='bool'),
        applications_and_url_filtering=dict(type='bool'),
        content_awareness=dict(type='bool'),
        detect_using_x_forward_for=dict(type='bool'),
        firewall=dict(type='bool'),
        implicit_cleanup_action=dict(type='str', choices=['drop', 'accept']),
        mobile_access=dict(type='bool'),
        shared=dict(type='bool'),
        tags=dict(type='list'),
        color=dict(type='str', choices=['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green',
                                        'khaki', 'orchid', 'dark orange', 'dark sea green', 'pink', 'turquoise', 'dark blue', 'firebrick', 'brown',
                                        'forest green', 'gold', 'dark gold', 'gray', 'dark gray', 'light green', 'lemon chiffon', 'coral', 'sea green',
                                        'sky blue', 'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange', 'red', 'sienna',
                                        'yellow']),
        comments=dict(type='str'),
        details_level=dict(type='str', choices=['uid', 'standard', 'full']),
        ignore_warnings=dict(type='bool'),
        ignore_errors=dict(type='bool')
    )
    argument_spec.update(checkpoint_argument_spec_for_objects)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    api_call_object = 'access-layer'

    result = api_call(module, api_call_object)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
