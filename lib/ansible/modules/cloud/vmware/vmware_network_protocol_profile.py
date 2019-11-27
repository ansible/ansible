#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Vishvarath Nayak vishvarath@gmail.com
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

#from typing import Optional, Any

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vmware_network_protocol_profile
short_description: create/remove network_protocol_profile to/from vCenter
description:
    - This module can be used to add/remove an IP Pool to/from vCenter
author:
- Vishvarath Nayak
notes:

requirements:
    - "python >= 2.6"
    - PyVmomi
'''

EXAMPLES = '''
- name: Add network protocol profile to vCenter
  vmware_network_protocol_profile:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter: '{{ datacenter_name }}'
    dvswitch: '{{ virtual_switch_name }}'
    network: '{{ network_name }}'
    ip_pool: '{{ ip_pool_name }}'
    gateway: '{{ gateway }}'
    ipPoolEnabled: False
    dhcpServerAvailable: False
    dns: '{{ [dns1,dns2] }}'
    subnetAddress: '{{ subnetAddress }}'
    netmask: '{{ network mask }}
    dnsDomain: '{{ domain fqdn }}'
    dnsSearchPath: '{{ search path }}'
    state: present
  delegate_to: localhost

- name : Delete network protocol profile to vCenter
  vmware_network_protocol_profile:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter: '{{ datacenter_name }}'
    ip_pool: '{{ ip_pool_name }}'
'''

RETURN = """
instance:
    description: metadata about the new IP pool
    returned: always
    type: dict
    sample: None
"""

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.vmware import get_all_objs, connect_to_api, vmware_argument_spec, find_datacenter_by_name, find_dvs_by_name, find_dvspg_by_name
from ansible.module_utils.basic import AnsibleModule


class vmware_network_protocol_profile(object):

    def __init__(self, module):
        self.module = module
        self.datacenter = module.params['datacenter']
        self.dvswitch = module.params['dvswitch']
        self.hostname = module.params['hostname']
        self.username = module.params['username']
        self.password = module.params['password']
        self.state = module.params['state']
        self.network = module.params['network']
        self.ip_pool = module.params['ip_pool']
        self.gateway = module.params['gateway']
        self.ipPoolEnabled = module.params['ipPoolEnabled']
        self.dhcpserverAvailable = module.params['dhcpServerAvailable']
        self.dns = module.params['dns']
        self.subnetAddress = module.params['subnetAddress']
        self.netmask = module.params['netmask']
        self.dnsDomain = module.params['dnsDomain']
        self.dnsSearchPath = module.params['dnsSearchPath']
        self.validate_certs = module.params['validate_certs']
        self.content = connect_to_api(module)
        self.dc_obj = find_datacenter_by_name(self.content, self.datacenter)
        self.ip_pool_obj = None
        self.dvsportgrp_obj = None
        self.dvswitch_obj = find_dvs_by_name(self.content, self.dvswitch)

    def select_ip_pool(self):
        pool_obj = None
        if self.dc_obj is None:
            self.module.fail_json(msg="Unable to find datacenter with name %s" % self.datacenter)
        pool_selections = self.content.ipPoolManager.QueryIpPools(self.dc_obj)
        for p in pool_selections:
            if p.name == self.ip_pool:
                pool_obj = p
                break
        return pool_obj

    def get_obj(self, vimtype, name, return_all=False):
        obj = list()
        container = self.content.viewManager.CreateContainerView(
            self.content.rootFolder, vimtype, True)

        for c in container.view:
            if name in [c.name, c._GetMoId()]:
                if return_all is False:
                    return c
                else:
                    obj.append(c)

        if len(obj) > 0:
            return obj
        else:
            # for backwards-compat
            return None

    def process_state(self):
        try:
            ippool_states = {
                'absent': {
                    'present': self.state_remove_ippool,
                    'absent': self.state_exit_unchanged,
                },
                'present': {
                    'present': self.state_exit_unchanged,
                    'absent': self.state_add_ippool,
                }
            }

            ippool_states[self.state][self.check_ippool_state()]()

        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=method_fault.msg)
        except Exception as e:
            self.module.fail_json(msg=str(e))

    def state_exit_unchanged(self):
        self.module.exit_json(changed=False)

    def state_remove_ippool(self):
        changed = True
        result = None
        try:
            self.ip_pool_obj = self.select_ip_pool()
            self.content.ipPoolManager.DestroyIpPool(self.dc_obj, self.ip_pool_obj.id, False)
            self.module.exit_json(changed=changed)
        except vim.fault.InvalidState as invalid_state:
            self.module.fail_json(msg="Unable to delete Ip Pool with name %s" % self.ip_pool)

    def state_add_ippool(self):
        changed = True
        if self.dc_obj is None:
            self.module.fail_json(msg="Unable to find datacenter with name %s" % self.datacenter)
        if self.dvswitch_obj is None:
            self.module.fail_json(msg="Unable to find distributed switch with name %s" % self.dvswitch)
        self.dvsportgrp_obj = find_dvspg_by_name(self.dvswitch_obj, self.network)

        IpPool_assoc = vim.vApp.IpPool.Association()
        IpPool_assoc.network = self.dvsportgrp_obj
        IpPool_assoc.networkName = self.network

        IpPool_config = vim.vApp.IpPool.IpPoolConfigInfo()
        IpPool_config.dhcpServerAvailable = self.dhcpserverAvailable
        IpPool_config.gateway = self.gateway
        IpPool_config.ipPoolEnabled = self.ipPoolEnabled
        IpPool_config.dns = self.dns
        IpPool_config.subnetAddress = self.subnetAddress
        IpPool_config.netmask = self.netmask

        IpPool_data = vim.vApp.IpPool()
        IpPool_data.name = self.ip_pool
        IpPool_data.ipv4Config = IpPool_config
        IpPool_data.dnsDomain = self.dnsDomain
        IpPool_data.dnsSearchPath = self.dnsSearchPath
        IpPool_data.networkAssociation = [IpPool_assoc]

        self.content.ipPoolManager.CreateIpPool(self.dc_obj, IpPool_data)

        self.module.exit_json(changed=changed)

    def check_ippool_state(self):

        ip_pools = self.content.ipPoolManager.QueryIpPools(self.dc_obj)
        for i in ip_pools:
            if i.name == self.ip_pool:
                self.ip_pool_obj = i

        if self.ip_pool_obj is None:
            return 'absent'
        else:
            return 'present'


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        datacenter=dict(required=True, type='str'),
	validate_certs=dict(required=False, type='bool'),
        dvswitch=dict(required=True, type='str'),
        network=dict(required=True, type='str'),
        ip_pool=dict(required=True, type='str'),
        gateway=dict(type='str'),
        ipPoolEnabled=dict(type='bool', default="True"),
        dhcpServerAvailable=dict(type='bool', default="True"),
        dns=dict(type='list'),
        subnetAddress=dict(type='str'),
        netmask=dict(type='str', default="255.255.255.0"),
        dnsDomain=dict(type='str'),
        dnsSearchPath=dict(type='str'),
        state=dict(default='present', choices=['present', 'absent'], type='str')))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    vmware_ip_pool = vmware_network_protocol_profile(module)
    vmware_ip_pool.process_state()


if __name__ == '__main__':
    main()
