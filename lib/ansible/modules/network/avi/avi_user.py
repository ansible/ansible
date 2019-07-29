#!/usr/bin/python
"""
# Created on Aug 2, 2018
#
# @author: Shrikant Chaudhari (shrikant.chaudhari@avinetworks.com) GitHub ID: gitshrikant
#
# module_check: supported
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
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_user
author: Shrikant Chaudhari (@gitshrikant) <shrikant.chaudhari@avinetworks.com>
short_description: Avi User Module
description:
    - This module can be used for creation, updation and deletion of a user.
version_added: 2.9
requirements: [ avisdk ]
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent", "present"]
        type: str
    name:
        description:
            - Full name of the user.
        required: true
        type: str
    obj_username:
        description:
            - Name that the user will supply when signing into Avi Vantage, such as jdoe or jdoe@avinetworks.com.
        required: true
        type: str
    obj_password:
        description:
            - You may either enter a case-sensitive password in this field for the new or existing user.
        required: true
        type: str
    email:
        description:
            - Email address of the user. This field is used when a user loses their password and requests to have it reset. See Password Recovery.
        type: str
    access:
        description:
            - Access settings (write, read, or no access) for each type of resource within Vantage.
        type: list
    is_superuser:
        description:
            - If the user will need to have the same privileges as the admin account, set it to true.
        type: bool
    is_active:
        description:
            - Activates the current user account.
        type: bool
    avi_api_update_method:
        description:
            - Default method for object update is HTTP PUT.
            - Setting to patch will override that behavior to use HTTP PATCH.
        default: put
        choices: ["post", "put", "patch"]
        type: str
    avi_api_patch_op:
        description:
            - Patch operation to use when using avi_api_update_method as patch.
        choices: ["add", "replace", "delete"]
        type: str
    user_profile_ref:
        description:
            - Refer user profile.
            - This can also be full URI same as it comes in response payload
        type: str
    default_tenant_ref:
        description:
            - Default tenant reference.
            - This can also be full URI same as it comes in response payload
        default: /api/tenant?name=admin
        type: str


extends_documentation_fragment:
    - avi
'''

EXAMPLES = '''
  - name: user creation
    avi_user:
      controller: ""
      username: ""
      password: ""
      api_version: ""
      name: "testuser"
      obj_username: "testuser"
      obj_password: "test123"
      email: "test@abc.test"
      access:
        - role_ref: "/api/role?name=Tenant-Admin"
          tenant_ref: "/api/tenant/admin#admin"
      user_profile_ref: "/api/useraccountprofile?name=Default-User-Account-Profile"
      is_active: true
      is_superuser: true
      default_tenant_ref: "/api/tenant?name=admin"

  - name: user creation
    avi_user:
      controller: ""
      username: ""
      password: ""
      api_version: ""
      name: "testuser"
      obj_username: "testuser2"
      obj_password: "password"
      email: "testuser2@abc.test"
      access:
        - role_ref: "https://192.0.2.10/api/role?name=Tenant-Admin"
          tenant_ref: "https://192.0.2.10/api/tenant/admin#admin"
      user_profile_ref: "https://192.0.2.10/api/useraccountprofile?name=Default-User-Account-Profile"
      is_active: true
      is_superuser: true
      default_tenant_ref: "https://192.0.2.10/api/tenant?name=admin"
'''

RETURN = '''
obj:
    description: Avi REST resource
    returned: success, changed
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible.module_utils.network.avi.avi import (
        avi_common_argument_spec, ansible_return, HAS_AVI)
    from ansible.module_utils.network.avi.ansible_utils import (
        avi_ansible_api)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
        name=dict(type='str', required=True),
        obj_username=dict(type='str', required=True),
        obj_password=dict(type='str', required=True, no_log=True),
        access=dict(type='list',),
        email=dict(type='str',),
        is_superuser=dict(type='bool',),
        is_active=dict(type='bool',),
        avi_api_update_method=dict(default='put',
                                   choices=['post', 'put', 'patch']),
        avi_api_patch_op=dict(choices=['add', 'replace', 'delete']),
        user_profile_ref=dict(type='str',),
        default_tenant_ref=dict(type='str', default='/api/tenant?name=admin'),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) or requests is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'user',
                           set([]))


if __name__ == '__main__':
    main()
