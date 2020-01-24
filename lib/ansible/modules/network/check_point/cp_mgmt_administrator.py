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
module: cp_mgmt_administrator
short_description: Manages administrator objects on Check Point over Web Services API
description:
  - Manages administrator objects on Check Point devices including creating, updating and removing objects.
  - All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  name:
    description:
      - Object name.
    type: str
    required: True
  authentication_method:
    description:
      - Authentication method.
    type: str
    choices: ['undefined', 'check point password', 'os password', 'securid', 'radius', 'tacacs', 'ad authentication']
  email:
    description:
      - Administrator email.
    type: str
  expiration_date:
    description:
      - Format, YYYY-MM-DD, YYYY-mm-ddThh,mm,ss.
    type: str
  multi_domain_profile:
    description:
      - Administrator multi-domain profile.
    type: str
  must_change_password:
    description:
      - True if administrator must change password on the next login.
    type: bool
  password:
    description:
      - Administrator password.
    type: str
  password_hash:
    description:
      - Administrator password hash.
    type: str
  permissions_profile:
    description:
      - Administrator permissions profile. Permissions profile should not be provided when multi-domain-profile is set to "Multi-Domain Super User" or
        "Domain Super User".
    type: list
    suboptions:
      profile:
        description:
          - Permission profile.
        type: str
  phone_number:
    description:
      - Administrator phone number.
    type: str
  radius_server:
    description:
      - RADIUS server object identified by the name or UID. Must be set when "authentication-method" was selected to be "RADIUS".
    type: str
  tacacs_server:
    description:
      - TACACS server object identified by the name or UID. Must be set when "authentication-method" was selected to be "TACACS".
    type: str
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
- name: add-administrator
  cp_mgmt_administrator:
    authentication_method: INTERNAL_PASSWORD
    email: admin@gmail.com
    must_change_password: false
    name: admin
    password: secret
    permissions_profile: read write all
    phone_number: 1800-800-800
    state: present

- name: set-administrator
  cp_mgmt_administrator:
    name: admin
    password: bew secret
    permissions_profile: read only profile
    state: present

- name: delete-administrator
  cp_mgmt_administrator:
    name: admin
    state: absent
"""

RETURN = """
cp_mgmt_administrator:
  description: The checkpoint object created or updated.
  returned: always, except when deleting the object.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_objects, api_call


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        authentication_method=dict(type='str', choices=['undefined', 'check point password',
                                                        'os password', 'securid', 'radius', 'tacacs', 'ad authentication']),
        email=dict(type='str'),
        expiration_date=dict(type='str'),
        multi_domain_profile=dict(type='str'),
        must_change_password=dict(type='bool'),
        password=dict(type='str'),
        password_hash=dict(type='str'),
        permissions_profile=dict(type='list', options=dict(
            profile=dict(type='str')
        )),
        phone_number=dict(type='str'),
        radius_server=dict(type='str'),
        tacacs_server=dict(type='str'),
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
    api_call_object = 'administrator'

    result = api_call(module, api_call_object)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
