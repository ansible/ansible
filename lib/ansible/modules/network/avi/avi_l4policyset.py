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
module: avi_l4policyset
author: Chaitanya Deshpande (@chaitanyaavi) <chaitanya.deshpande@avinetworks.com>

short_description: Module for setup of L4PolicySet Avi RESTful Object
description:
    - This module is used to configure L4PolicySet object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.6"
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
        default: put
        choices: ["put", "patch"]
    avi_api_patch_op:
        description:
            - Patch operation to use when using avi_api_update_method as patch.
        choices: ["add", "replace", "delete"]
    created_by:
        description:
            - Creator name.
            - Field introduced in 17.2.7.
    description:
        description:
            - Field introduced in 17.2.7.
    is_internal_policy:
        description:
            - Field introduced in 17.2.7.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    l4_connection_policy:
        description:
            - Policy to apply when a new transport connection is setup.
            - Field introduced in 17.2.7.
    name:
        description:
            - Name of the l4 policy set.
            - Field introduced in 17.2.7.
        required: true
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
            - Field introduced in 17.2.7.
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Id of the l4 policy set.
            - Field introduced in 17.2.7.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
- name: Example to create L4PolicySet object
  avi_l4policyset:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_l4policyset
"""

RETURN = '''
obj:
    description: L4PolicySet (api/l4policyset) object
    returned: success, changed
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.module_utils.network.avi.avi import (
        avi_common_argument_spec, avi_ansible_api, HAS_AVI)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
        avi_api_update_method=dict(default='put',
                                   choices=['put', 'patch']),
        avi_api_patch_op=dict(choices=['add', 'replace', 'delete']),
        created_by=dict(type='str',),
        description=dict(type='str',),
        is_internal_policy=dict(type='bool',),
        l4_connection_policy=dict(type='dict',),
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
            'Avi python API SDK (avisdk>=17.1) or requests is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'l4policyset',
                           set([]))


if __name__ == '__main__':
    main()
