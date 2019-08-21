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
module: cp_mgmt_opsec_application
short_description: Manages opsec-application objects on Checkpoint over Web Services API
description:
  - Manages opsec-application objects on Checkpoint devices including creating, updating and removing objects.
    All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  name:
    description:
      - Object name.
    type: str
    required: True
  host:
    description:
      - The host where the server is running. Pre-define the host as a network object.
    type: str
  cpmi:
    description:
      - Used to setup the CPMI client entity.
    type: list
    suboptions:
      administrator_profile:
        description:
          - A profile to set the log reading permissions by for the client entity.
        type: str
        choices: ['read only all', 'read write all', 'super user']
      enabled:
        description:
          - Whether to enable this client entity on the Opsec Application.
        type: bool
      use_administrator_credentials:
        description:
          - Whether to use the Admin's credentials to login to the security management server.
        type: bool
  lea:
    description:
      - Used to setup the LEA client entity.
    type: list
    suboptions:
      access_permissions:
        description:
          - Log reading permissions for the LEA client entity.
        type: str
        choices: ['show all', 'hide all', 'by profile']
      administrator_profile:
        description:
          - A profile to set the log reading permissions by for the client entity.
        type: str
        choices: ['read only all', 'read write all', 'super user']
      enabled:
        description:
          - Whether to enable this client entity on the Opsec Application.
        type: bool
  one_time_password:
    description:
      - A password required for establishing a Secure Internal Communication (SIC).
    type: str
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
- name: add-opsec-application
  cp_mgmt_opsec_application:
    cpmi:
      administrator_profile: Super User
      enabled: 'true'
      use_administrator_credentials: 'false'
    host: SomeHost
    lea:
      enabled: 'false'
    name: MyOpsecApplication
    one_time_password: SomePassword

- name: set-opsec-application
  cp_mgmt_opsec_application:
    cpmi:
      enabled: 'false'
    lea:
      access_permissions: Show All
      enabled: 'true'
    name: MyOpsecApplication
    new_name: MyUpdatedOpsecapplication

- name: delete-opsec-application
  cp_mgmt_opsec_application:
    name: MySecondOpsecApplication
    state: absent
"""

RETURN = """
cp_mgmt_opsec_application:
  description: The checkpoint object created or updated.
  returned: always, except when deleting the object.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_objects, api_call


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        host=dict(type='str'),
        cpmi=dict(type='list', options=dict(
            administrator_profile=dict(type='str', choices=['read only all', 'read write all', 'super user']),
            enabled=dict(type='bool'),
            use_administrator_credentials=dict(type='bool')
        )),
        lea=dict(type='list', options=dict(
            access_permissions=dict(type='str', choices=['show all', 'hide all', 'by profile']),
            administrator_profile=dict(type='str', choices=['read only all', 'read write all', 'super user']),
            enabled=dict(type='bool')
        )),
        one_time_password=dict(type='str'),
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
    api_call_object = 'opsec-application'

    result = api_call(module, api_call_object)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
