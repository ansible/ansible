#!/usr/bin/python
#
# Created on Aug 25, 2016
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
# Avi Version: 17.1.1
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_networksecuritypolicy
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of NetworkSecurityPolicy Avi RESTful Object
description:
    - This module is used to configure NetworkSecurityPolicy object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.4"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent","present"]
    cloud_config_cksum:
        description:
            - Checksum of cloud configuration for network sec policy.
            - Internally set by cloud connector.
    created_by:
        description:
            - Creator name.
    description:
        description:
            - User defined description for the object.
    name:
        description:
            - Name of the object.
    rules:
        description:
            - List of networksecurityrule.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
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
  - name: Create a network security policy to block clients represented by ip group known_attackers
    avi_networksecuritypolicy:
      controller: ''
      username: ''
      password: ''
      name: vs-gurutest-ns
      rules:
      - action: NETWORK_SECURITY_POLICY_ACTION_TYPE_DENY
        age: 0
        enable: true
        index: 1
        log: false
        match:
          client_ip:
            group_refs:
            - Demo:known_attackers
            match_criteria: IS_IN
        name: Rule 1
      tenant_ref: Demo
'''
RETURN = '''
obj:
    description: NetworkSecurityPolicy (api/networksecuritypolicy) object
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
        cloud_config_cksum=dict(type='str',),
        created_by=dict(type='str',),
        description=dict(type='str',),
        name=dict(type='str',),
        rules=dict(type='list',),
        tenant_ref=dict(type='str',),
        url=dict(type='str',),
        uuid=dict(type='str',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'networksecuritypolicy',
                           set([]))

if __name__ == '__main__':
    main()
