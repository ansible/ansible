#!/usr/bin/python
#
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
# Avi Version: 18.2.2
#
# Copyright: (c) 2017 Gaurav Rastogi, <grastogi@avinetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_securitypolicy
author: Chaitanya Deshpande (@chaitanyaavi) <chaitanya.deshpande@avinetworks.com>

short_description: Module for setup of SecurityPolicy Avi RESTful Object
description:
    - This module is used to configure SecurityPolicy object
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
            - Security policy is used to specify various configuration information used to perform distributed denial of service (ddos) attacks detection and
            - mitigation.
            - Field introduced in 18.2.1.
    dns_attacks:
        description:
            - Attacks utilizing the dns protocol operations.
            - Field introduced in 18.2.1.
    dns_policy_index:
        description:
            - Index of the dns policy to use for the mitigation rules applied to the dns attacks.
            - Field introduced in 18.2.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
        required: true
    name:
        description:
            - The name of the security policy.
            - Field introduced in 18.2.1.
        required: true
    network_security_policy_index:
        description:
            - Index of the network security policy to use for the mitigation rules applied to the attacks.
            - Field introduced in 18.2.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
        required: true
    oper_mode:
        description:
            - Mode of dealing with the attacks - perform detection only, or detect and mitigate the attacks.
            - Enum options - DETECTION, MITIGATION.
            - Field introduced in 18.2.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as DETECTION.
    tcp_attacks:
        description:
            - Attacks utilizing the tcp protocol operations.
            - Field introduced in 18.2.1.
    tenant_ref:
        description:
            - Tenancy of the security policy.
            - It is a reference to an object of type tenant.
            - Field introduced in 18.2.1.
    udp_attacks:
        description:
            - Attacks utilizing the udp protocol operations.
            - Field introduced in 18.2.1.
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - The uuid of the security policy.
            - Field introduced in 18.2.1.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
- name: Example to create SecurityPolicy object
  avi_securitypolicy:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_securitypolicy
"""

RETURN = '''
obj:
    description: SecurityPolicy (api/securitypolicy) object
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
        dns_attacks=dict(type='dict',),
        dns_policy_index=dict(type='int', required=True),
        name=dict(type='str', required=True),
        network_security_policy_index=dict(type='int', required=True),
        oper_mode=dict(type='str',),
        tcp_attacks=dict(type='dict',),
        tenant_ref=dict(type='str',),
        udp_attacks=dict(type='dict',),
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
    return avi_ansible_api(module, 'securitypolicy',
                           set([]))


if __name__ == '__main__':
    main()
