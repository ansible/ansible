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
module: avi_protocolparser
author: Chaitanya Deshpande (@chaitanyaavi) <chaitanya.deshpande@avinetworks.com>

short_description: Module for setup of ProtocolParser Avi RESTful Object
description:
    - This module is used to configure ProtocolParser object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.9"
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
    description:
        description:
            - Description of the protocol parser.
            - Field introduced in 18.2.3.
    name:
        description:
            - Name of the protocol parser.
            - Field introduced in 18.2.3.
        required: true
    parser_code:
        description:
            - Command script provided inline.
            - Field introduced in 18.2.3.
        required: true
    tenant_ref:
        description:
            - Tenant uuid of the protocol parser.
            - It is a reference to an object of type tenant.
            - Field introduced in 18.2.3.
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Uuid of the protocol parser.
            - Field introduced in 18.2.3.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
- name: Example to create ProtocolParser object
  avi_protocolparser:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_protocolparser
"""

RETURN = '''
obj:
    description: ProtocolParser (api/protocolparser) object
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
        description=dict(type='str',),
        name=dict(type='str', required=True),
        parser_code=dict(type='str', required=True),
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
    return avi_ansible_api(module, 'protocolparser',
                           set([]))


if __name__ == '__main__':
    main()
