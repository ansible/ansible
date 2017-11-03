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
module: avi_stringgroup
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of StringGroup Avi RESTful Object
description:
    - This module is used to configure StringGroup object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.4"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent","present"]
    description:
        description:
            - User defined description for the object.
    kv:
        description:
            - Configure key value in the string group.
    name:
        description:
            - Name of the string group.
        required: true
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    type:
        description:
            - Type of stringgroup.
            - Enum options - SG_TYPE_STRING, SG_TYPE_KEYVAL.
            - Default value when not specified in API or module is interpreted by Avi Controller as SG_TYPE_STRING.
        required: true
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Uuid of the string group.
extends_documentation_fragment:
    - avi
'''


EXAMPLES = '''
  - name: Create a string group configuration
    avi_stringgroup:
      controller: ''
      password: ''
      username: ''
      kv:
      - key: text/html
      - key: text/xml
      - key: text/plain
      - key: text/css
      - key: text/javascript
      - key: application/javascript
      - key: application/x-javascript
      - key: application/xml
      - key: application/pdf
      name: System-Compressible-Content-Types
      tenant_ref: admin
      type: SG_TYPE_STRING
'''
RETURN = '''
obj:
    description: StringGroup (api/stringgroup) object
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
        description=dict(type='str',),
        kv=dict(type='list',),
        name=dict(type='str', required=True),
        tenant_ref=dict(type='str',),
        type=dict(type='str', required=True),
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
    return avi_ansible_api(module, 'stringgroup',
                           set([]))

if __name__ == '__main__':
    main()
