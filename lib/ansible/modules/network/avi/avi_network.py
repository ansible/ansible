#!/usr/bin/python
#
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
# Avi Version: 17.1.1
#
# Copyright: (c) 2017 Gaurav Rastogi, <grastogi@avinetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_network
author: Gaurav Rastogi (@grastogi23) <grastogi@avinetworks.com>

short_description: Module for setup of Network Avi RESTful Object
description:
    - This module is used to configure Network object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.4"
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
    cloud_ref:
        description:
            - It is a reference to an object of type cloud.
    configured_subnets:
        description:
            - List of subnet.
    dhcp_enabled:
        description:
            - Select the ip address management scheme for this network.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
        type: bool
    exclude_discovered_subnets:
        description:
            - When selected, excludes all discovered subnets in this network from consideration for virtual service placement.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    name:
        description:
            - Name of the object.
        required: true
    synced_from_se:
        description:
            - Boolean flag to set synced_from_se.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Unique object identifier of the object.
    vcenter_dvs:
        description:
            - Boolean flag to set vcenter_dvs.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
        type: bool
    vimgrnw_ref:
        description:
            - It is a reference to an object of type vimgrnwruntime.
    vrf_context_ref:
        description:
            - It is a reference to an object of type vrfcontext.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
- name: Example to create Network object
  avi_network:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_network
"""

RETURN = '''
obj:
    description: Network (api/network) object
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
        cloud_ref=dict(type='str',),
        configured_subnets=dict(type='list',),
        dhcp_enabled=dict(type='bool',),
        exclude_discovered_subnets=dict(type='bool',),
        name=dict(type='str', required=True),
        synced_from_se=dict(type='bool',),
        tenant_ref=dict(type='str',),
        url=dict(type='str',),
        uuid=dict(type='str',),
        vcenter_dvs=dict(type='bool',),
        vimgrnw_ref=dict(type='str',),
        vrf_context_ref=dict(type='str',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'network',
                           set([]))


if __name__ == '__main__':
    main()
