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
module: avi_network
author: Gaurav Rastogi (grastogi@avinetworks.com)

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
        choices: ["absent","present"]
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
    exclude_discovered_subnets:
        description:
            - When selected, excludes all discovered subnets in this network from consideration for virtual service placement.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    name:
        description:
            - Name of the object.
        required: true
    synced_from_se:
        description:
            - Boolean flag to set synced_from_se.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
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
    from ansible.module_utils.avi import (
        avi_common_argument_spec, HAS_AVI, avi_ansible_api)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
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
