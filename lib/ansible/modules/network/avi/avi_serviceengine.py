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
module: avi_serviceengine
author: Gaurav Rastogi (grastogi@avinetworks.com)

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
        choices: ["absent","present"]
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
    container_type:
        description:
            - Enum options - container_type_bridge, container_type_host, container_type_host_dpdk.
            - Default value when not specified in API or module is interpreted by Avi Controller as CONTAINER_TYPE_HOST.
    controller_created:
        description:
            - Boolean flag to set controller_created.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    controller_ip:
        description:
            - Controller_ip of serviceengine.
    data_vnics:
        description:
            - List of vnic.
    enable_state:
        description:
            - Inorder to disable se set this field appropriately.
            - Enum options - SE_STATE_ENABLED, SE_STATE_DISABLED_FOR_PLACEMENT, SE_STATE_DISABLED.
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
    from ansible.module_utils.avi import (
        avi_common_argument_spec, HAS_AVI, avi_ansible_api)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
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
            'Avi python API SDK (avisdk>=17.1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'serviceengine',
                           set([]))

if __name__ == '__main__':
    main()
