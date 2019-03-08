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
    old_password:
        description:
            - Old password for update password or default password for bootstrap.

extends_documentation_fragment:
    - avi
'''

EXAMPLES = '''

  - name: Update user password
    avi_useraccount:
      controller: ""
      username: ""
      password: new_password
      old_password: ""
      api_version: ""

  - name: Update user password using avi_credentials
    avi_useraccount:
      avi_credentials: ""
      old_password: ""
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
        avi_common_argument_spec, ansible_return, HAS_AVI)
    from avi.sdk.avi_api import ApiSession, AviCredentials
    from avi.sdk.utils.ansible_utils import avi_obj_cmp, cleanup_absent_fields

except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        old_password=dict(type='str', required=True, no_log=True)
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(argument_spec=argument_specs)

    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))

    api_creds = AviCredentials()
    api_creds.update_from_ansible_module(module)
    password_updated = False
    old_password = module.params.get('old_password')
    data = {
        'old_password': old_password,
        'password': api_creds.password
    }
    password_changed = False
    try:
        api = ApiSession.get_session(
            api_creds.controller, api_creds.username,
            password=api_creds.password, timeout=api_creds.timeout,
            tenant=api_creds.tenant, tenant_uuid=api_creds.tenant_uuid,
            token=api_creds.token, port=api_creds.port)
        password_changed = True
        return ansible_return(module, None, False, req=data)
    except Exception:
        pass

    if not password_changed:
        api = ApiSession.get_session(
            api_creds.controller, api_creds.username, password=old_password,
            timeout=api_creds.timeout, tenant=api_creds.tenant,
            tenant_uuid=api_creds.tenant_uuid, token=api_creds.token,
            port=api_creds.port)
        rsp = api.put('useraccount', data=data)
        if rsp:
            return ansible_return(module, rsp, True, req=data)
        return module.exit_json(changed=False, obj=data)


if __name__ == '__main__':
    main()
