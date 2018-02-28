#!/usr/bin/python
#
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
#
# Copyright: (c) 2017 Gaurav Rastogi, <grastogi@avinetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_errorpagebody
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of ErrorPageBody Avi RESTful Object
description:
    - This module is used to configure ErrorPageBody object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.5"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent", "present"]
    avi_api_update_method:
        description:
            - Default method for object update is HTTP PUT.
            - Setting to patch will override that behavior to use HTTP PATCH.
        version_added: "2.5"
        default: put
        choices: ["put", "patch"]
    avi_api_patch_op:
        description:
            - Patch operation to use when using avi_api_update_method as patch.
        version_added: "2.5"
        choices: ["add", "replace", "delete"]
    error_page_body:
        description:
            - Error page body sent to client when match.
            - Field introduced in 17.2.4.
    name:
        description:
            - Field introduced in 17.2.4.
        required: true
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
            - Field introduced in 17.2.4.
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Field introduced in 17.2.4.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
- name: Example to create ErrorPageBody object
  avi_errorpagebody:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_errorpagebody
"""

RETURN = '''
obj:
    description: ErrorPageBody (api/errorpagebody) object
    returned: success, changed
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.module_utils.network.avi.avi import (
        avi_common_argument_spec, HAS_AVI, avi_ansible_api)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
        avi_api_update_method=dict(default='put',
                                   choices=['put', 'patch']),
        avi_api_patch_op=dict(choices=['add', 'replace', 'delete']),
        error_page_body=dict(type='str',),
        name=dict(type='str', required=True),
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
    return avi_ansible_api(module, 'errorpagebody',
                           set([]))

if __name__ == '__main__':
    main()
