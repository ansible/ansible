#!/usr/bin/python
"""
# Created on July 24, 2017
#
# @author: Vilian Atmadzhov (vilian.atmadzhov@paddypowerbetfair.com) GitHub ID: vivobg
#
# module_check: not supported
#
# Copyright: (c) 2017 Gaurav Rastogi, <grastogi@avinetworks.com>
#                     Vilian Atmadzhov, <vilian.atmadzhov@paddypowerbetfair.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
"""


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: avi_api_version
author: Vilian Atmadzhov (@vivobg) <vilian.atmadzhov@paddypowerbetfair.com>

short_description: Avi API Version Module
description:
    - This module can be used to obtain the version of the Avi REST API. U(https://avinetworks.com/)
version_added: 2.5
requirements: [ avisdk ]
options: {}
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
        avi_common_argument_spec, ansible_return, HAS_AVI)
    from ansible.module_utils.network.avi.avi_api import (
        ApiSession, AviCredentials)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict()
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(argument_spec=argument_specs)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) or requests is not installed. '
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
        module.fail_json(msg=("Unable to get an AVI session. %s" % e))


if __name__ == '__main__':
    main()
