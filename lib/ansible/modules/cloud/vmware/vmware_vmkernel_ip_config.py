#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Joseph Callen <jcallen () csc.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vmware_vmkernel_ip_config
short_description: Configure the VMkernel IP Address
description:
    - Configure the VMkernel IP Address
version_added: 2.0
author: "Joseph Callen (@jcpowermac), Russell Teague (@mtnbikenc)"
notes:
    - Tested on vSphere 5.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    vmk_name:
        description:
            - VMkernel interface name
        required: True
    ip_address:
        description:
            - IP address to assign to VMkernel interface
        required: True
    subnet_mask:
        description:
            - Subnet Mask to assign to VMkernel interface
        required: True
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
# Example command from Ansible Playbook

- name: Configure IP address on ESX host
  local_action:
    module: vmware_vmkernel_ip_config
    hostname: esxi_hostname
    username: esxi_username
    password: esxi_password
    vmk_name: vmk0
    ip_address: 10.0.0.10
    subnet_mask: 255.255.255.0
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import HAS_PYVMOMI, connect_to_api, get_all_objs, vmware_argument_spec


def configure_vmkernel_ip_address(host_system, vmk_name, ip_address, subnet_mask):

    host_config_manager = host_system.configManager
    host_network_system = host_config_manager.networkSystem

    for vnic in host_network_system.networkConfig.vnic:
        if vnic.device == vmk_name:
            spec = vnic.spec
            if spec.ip.ipAddress != ip_address:
                spec.ip.dhcp = False
                spec.ip.ipAddress = ip_address
                spec.ip.subnetMask = subnet_mask
                host_network_system.UpdateVirtualNic(vmk_name, spec)
                return True
    return False


def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(vmk_name=dict(required=True, type='str'),
                         ip_address=dict(required=True, type='str'),
                         subnet_mask=dict(required=True, type='str')))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    vmk_name = module.params['vmk_name']
    ip_address = module.params['ip_address']
    subnet_mask = module.params['subnet_mask']

    try:
        content = connect_to_api(module, False)
        host = get_all_objs(content, [vim.HostSystem])
        if not host:
            module.fail_json(msg="Unable to locate Physical Host.")
        host_system = host.keys()[0]
        changed = configure_vmkernel_ip_address(host_system, vmk_name, ip_address, subnet_mask)
        module.exit_json(changed=changed)
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
