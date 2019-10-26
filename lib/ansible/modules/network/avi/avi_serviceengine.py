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
module: avi_serviceengine
author: Gaurav Rastogi (@grastogi23) <grastogi@avinetworks.com>

short_description: Module for setup of ServiceEngine Avi RESTful Object
description:
    - This module is used to configure ServiceEngine object
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
    availability_zone:
        description:
            - Availability_zone of serviceengine.
    cloud_ref:
        description:
            - It is a reference to an object of type cloud.
    container_mode:
        description:
            - Boolean flag to set container_mode.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    container_type:
        description:
            - Enum options - container_type_bridge, container_type_host, container_type_host_dpdk.
            - Default value when not specified in API or module is interpreted by Avi Controller as CONTAINER_TYPE_HOST.
    controller_created:
        description:
            - Boolean flag to set controller_created.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    controller_ip:
        description:
            - Controller_ip of serviceengine.
    data_vnics:
        description:
            - List of vnic.
    enable_state:
        description:
            - Inorder to disable se set this field appropriately.
            - Enum options - SE_STATE_ENABLED, SE_STATE_DISABLED_FOR_PLACEMENT, SE_STATE_DISABLED, SE_STATE_DISABLED_FORCE.
            - Default value when not specified in API or module is interpreted by Avi Controller as SE_STATE_ENABLED.
    flavor:
        description:
            - Flavor of serviceengine.
    host_ref:
        description:
            - It is a reference to an object of type vimgrhostruntime.
    hypervisor:
        description:
            - Enum options - default, vmware_esx, kvm, vmware_vsan, xen.
    mgmt_vnic:
        description:
            - Vnic settings for serviceengine.
    name:
        description:
            - Name of the object.
            - Default value when not specified in API or module is interpreted by Avi Controller as VM name unknown.
    resources:
        description:
            - Seresources settings for serviceengine.
    se_group_ref:
        description:
            - It is a reference to an object of type serviceenginegroup.
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

EXAMPLES = """
- name: Example to create ServiceEngine object
  avi_serviceengine:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_serviceengine
"""

RETURN = '''
obj:
    description: ServiceEngine (api/serviceengine) object
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
        availability_zone=dict(type='str',),
        cloud_ref=dict(type='str',),
        container_mode=dict(type='bool',),
        container_type=dict(type='str',),
        controller_created=dict(type='bool',),
        controller_ip=dict(type='str',),
        data_vnics=dict(type='list',),
        enable_state=dict(type='str',),
        flavor=dict(type='str',),
        host_ref=dict(type='str',),
        hypervisor=dict(type='str',),
        mgmt_vnic=dict(type='dict',),
        name=dict(type='str',),
        resources=dict(type='dict',),
        se_group_ref=dict(type='str',),
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
    return avi_ansible_api(module, 'serviceengine',
                           set([]))


if __name__ == '__main__':
    main()
