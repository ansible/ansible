#!/usr/bin/python
#
# Created on Aug 25, 2016
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
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
module: avi_microservicegroup
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of MicroServiceGroup Avi RESTful Object
description:
    - This module is used to configure MicroServiceGroup object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.4"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent","present"]
    created_by:
        description:
            - Creator name.
    description:
        description:
            - User defined description for the object.
    name:
        description:
            - Name of the microservice group.
        required: true
    service_refs:
        description:
            - Configure microservice(es).
            - It is a reference to an object of type microservice.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Uuid of the microservice group.
extends_documentation_fragment:
    - avi
'''


EXAMPLES = '''
  - name: Create a Microservice Group that can be used for setting up Network security policy
    avi_microservicegroup:
      controller: ''
      username: ''
      password: ''
      description: Group created by my Secure My App UI.
      name: vs-msg-marketing
      tenant_ref: admin
'''
RETURN = '''
obj:
    description: MicroServiceGroup (api/microservicegroup) object
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
        created_by=dict(type='str',),
        description=dict(type='str',),
        name=dict(type='str', required=True),
        service_refs=dict(type='list',),
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
    return avi_ansible_api(module, 'microservicegroup',
                           set([]))

if __name__ == '__main__':
    main()
