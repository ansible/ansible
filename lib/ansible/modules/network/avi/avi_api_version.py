#!/usr/bin/python
"""
# Created on July 24, 2017
#
# @author: Vilian Atmadzhov (vilian.atmadzhov@paddypowerbetfair.com) GitHub ID: vivobg
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
module: avi_api_version
author: Vilian Atmadzhov (vilian.atmadzhov@paddypowerbetfair.com)

short_description: Avi API Version Module
description:
    - This module can be used to obtain the version of the Avi REST API. U(https://avinetworks.com/)
version_added: 2.5
requirements: [ avisdk ]
options:
    tenant:
        description:
            - Avi Tenant.
        required: true
extends_documentation_fragment:
    - avi
'''

EXAMPLES = '''
  - name: Get AVI API version
    avi_api_version:
      controller: ""
      username: ""
      password: ""
      tenant: ""
    register: avi_controller_version
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
        avi_common_argument_spec, HAS_AVI, AviCredentials)
    from avi.sdk.avi_api import ApiSession
except ImportError:
    HAS_AVI = False


def main():
    module = AnsibleModule(argument_spec=avi_common_argument_spec())
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    try:
        api_creds = AviCredentials()
        api_creds.update_from_ansible_module(module)
        api = ApiSession.get_session(
            api_creds.controller, api_creds.username,
            password=api_creds.password,
            timeout=api_creds.timeout, tenant=api_creds.tenant,
            tenant_uuid=api_creds.tenant_uuid, token=api_creds.token,
            port=api_creds.port)

        remote_api_version = api.remote_api_version
        remote = {}
        for key in remote_api_version.keys():
            remote[key.lower()] = remote_api_version[key]
        api.close()
        module.exit_json(changed=False, obj=remote)
    except Exception as e:
        module.fail_json(msg="Unable to get an AVI session. {}".format(e))

if __name__ == '__main__':
    main()
