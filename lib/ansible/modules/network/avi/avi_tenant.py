#!/usr/bin/python
#
# Created on Aug 25, 2016
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
# Avi Version: 16.3.8
#
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: avi_tenant
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of Tenant Avi RESTful Object
description:
    - This module is used to configure Tenant object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.3"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent","present"]
    config_settings:
        description:
            - Tenantconfiguration settings for tenant.
    created_by:
        description:
            - Creator of this tenant.
    description:
        description:
            - User defined description for the object.
    local:
        description:
            - Boolean flag to set local.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
    name:
        description:
            - Name of the object.
        required: true
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Unique object identifier of the object.
extends_documentation_fragment:
    - avi
'''


EXAMPLES = '''
  - name: Create Tenant using Service Engines in provider mode
    avi_tenant:
      controller: ''
      password: ''
      username: ''
      config_settings:
        se_in_provider_context: false
        tenant_access_to_provider_se: true
        tenant_vrf: false
      description: VCenter, Open Stack, AWS Virtual services
      local: true
      name: Demo
'''
RETURN = '''
obj:
    description: Tenant (api/tenant) object
    returned: success, changed
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible.module_utils.avi import (
        avi_common_argument_spec, HAS_AVI, avi_ansible_api)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
        config_settings=dict(type='dict',),
        created_by=dict(type='str',),
        description=dict(type='str',),
        local=dict(type='bool',),
        name=dict(type='str', required=True),
        url=dict(type='str',),
        uuid=dict(type='str',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=16.3.5.post1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'tenant',
                           set([]))


if __name__ == '__main__':
    main()
