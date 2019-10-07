#!/usr/bin/python
"""
# Created on Aug 12, 2016
#
# @author: Gaurav Rastogi (grastogi@avinetworks.com) GitHub ID: grastogi23
#
# module_check: not supported
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


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_useraccount
author: Chaitanya Deshpande (@chaitanyaavi) <chaitanya.deshpande@avinetworks.com>
short_description: Avi UserAccount Module
description:
    - This module can be used for updating the password of a user.
    - This module is useful for setting up admin password for Controller bootstrap.
version_added: 2.6
requirements: [ avisdk ]
options:
    full_name:
        description:
            - To set the full name for useraccount.
        type: str
    email:
        description:
            - To set email address for useraccount.
        type: str
    old_password:
        description:
            - Old password for update password or default password for bootstrap.
        required: true
        type: str
    force_change:
        description:
            - If specifically set to true then old password is tried first for controller and then the new password is
              tried. If not specified this flag then the new password is tried first.
        version_added: "2.9"
        type: bool


extends_documentation_fragment:
    - avi
'''

EXAMPLES = '''
  - name: Update user password
    avi_useraccount:
      controller: ""
      username: ""
      password: ""
      full_name: "abc xyz"
      email: "abc@xyz.com"
      old_password: ""
      api_version: ""
      force_change: false

  - name: Update user password using avi_credentials
    avi_useraccount:
      avi_credentials: ""
      old_password: ""
      force_change: false
'''

RETURN = '''
obj:
    description: Avi REST resource
    returned: success, changed
    type: dict
'''

import json
import time
from ansible.module_utils.basic import AnsibleModule
from copy import deepcopy

try:
    from ansible.module_utils.network.avi.avi import (
        avi_common_argument_spec, ansible_return, avi_obj_cmp,
        cleanup_absent_fields, HAS_AVI)
    from ansible.module_utils.network.avi.avi_api import (
        ApiSession, AviCredentials)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        full_name=dict(type='str'),
        email=dict(type='str'),
        old_password=dict(type='str', required=True, no_log=True),
        # Flag to specify priority of old/new password while establishing session with controller.
        # To handle both Saas and conventional (Entire state in playbook) scenario.
        force_change=dict(type='bool', default=False)
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(argument_spec=argument_specs)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) or requests is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    api_creds = AviCredentials()
    api_creds.update_from_ansible_module(module)
    full_name = module.params.get('full_name')
    email = module.params.get('email')
    old_password = module.params.get('old_password')
    force_change = module.params.get('force_change', False)
    data = {
        'old_password': old_password,
        'password': api_creds.password
    }
    if full_name:
        data['full_name'] = full_name
    if email:
        data['email'] = email
    api = None
    if not force_change:
        # check if the new password is already set.
        try:
            api = ApiSession.get_session(
                api_creds.controller, api_creds.username,
                password=api_creds.password, timeout=api_creds.timeout,
                tenant=api_creds.tenant, tenant_uuid=api_creds.tenant_uuid,
                token=api_creds.token, port=api_creds.port)
            data['old_password'] = api_creds.password
        except Exception:
            # create a new session using the old password.
            pass
    if not api:
        api = ApiSession.get_session(
            api_creds.controller, api_creds.username,
            password=old_password, timeout=api_creds.timeout,
            tenant=api_creds.tenant, tenant_uuid=api_creds.tenant_uuid,
            token=api_creds.token, port=api_creds.port)
    rsp = api.put('useraccount', data=data)
    return ansible_return(module, rsp, True, req=data)


if __name__ == '__main__':
    main()
