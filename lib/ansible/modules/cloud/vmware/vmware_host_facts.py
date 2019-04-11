#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Wei Gao <gaowei3@qq.com>
# Copyright: (c) 2018, Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: vmware_host_facts
short_description: Gathers facts about remote ESXi hostsystem
description:
    - This module can be used to gathers facts like CPU, memory, datastore, network and system etc. about ESXi host system.
    - Please specify hostname or IP address of ESXi host system as C(hostname).
    - If hostname or IP address of vCenter is provided as C(hostname) and C(esxi_hostname) is not specified, then the
      module will throw an error.
    - VSAN facts added in 2.7 version.
version_added: 2.5
author:
    - Wei Gao (@woshihaoren)
requirements:
    - python >= 2.6
    - PyVmomi
options:
  esxi_hostname:
    description:
    - ESXi hostname.
    - Host facts about the specified ESXi server will be returned.
    - By specifying this option, you can select which ESXi hostsystem is returned if connecting to a vCenter.
    version_added: 2.8
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Gather vmware host facts
  vmware_host_facts:
    hostname: "{{ esxi_server }}"
    username: "{{ esxi_username }}"
    password: "{{ esxi_password }}"
  register: host_facts
  delegate_to: localhost

- name: Gather vmware host facts from vCenter
  vmware_host_facts:
    hostname: "{{ vcenter_server }}"
    username: "{{ vcenter_user }}"
    password: "{{ vcenter_pass }}"
    esxi_hostname: "{{ esxi_hostname }}"
  register: host_facts
  delegate_to: localhost

- name: Get VSAN Cluster UUID from host facts
  vmware_host_facts:
    hostname: "{{ esxi_server }}"
    username: "{{ esxi_username }}"
    password: "{{ esxi_password }}"
  register: host_facts
- set_fact:
    cluster_uuid: "{{ host_facts['ansible_facts']['vsan_cluster_uuid'] }}"
'''

RETURN = r'''
ansible_facts:
  description: system info about the host machine
  returned: always
  type: dict
  sample:
    {
        "ansible_all_ipv4_addresses": [
            "10.76.33.200"
        ],
        "ansible_bios_date": "2011-01-01T00:00:00+00:00",
        "ansible_bios_version": "0.5.1",
        "ansible_datastore": [
            {
                "free": "11.63 GB",
                "name": "datastore1",
                "total": "12.50 GB"
            }
        ],
        "ansible_distribution": "VMware ESXi",
        "ansible_distribution_build": "4887370",
        "ansible_distribution_version": "6.5.0",
        "ansible_hostname": "10.76.33.100",
        "ansible_interfaces": [
            "vmk0"
        ],
        "ansible_memfree_mb": 2702,
        "ansible_memtotal_mb": 4095,
        "ansible_os_type": "vmnix-x86",
        "ansible_processor": "Intel Xeon E312xx (Sandy Bridge)",
        "ansible_processor_cores": 2,
        "ansible_processor_count": 2,
        "ansible_processor_vcpus": 2,
        "ansible_product_name": "KVM",
        "ansible_product_serial": "NA",
        "ansible_system_vendor": "Red Hat",
        "ansible_vmk0": {
            "device": "vmk0",
            "ipv4": {
                "address": "10.76.33.100",
                "netmask": "255.255.255.0"
            },
            "macaddress": "52:54:00:56:7d:59",
            "mtu": 1500
        },
        "vsan_cluster_uuid": null,
        "vsan_node_uuid": null,
        "vsan_health": "unknown",
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.formatters import bytes_to_human
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, find_obj

try:
    from pyVmomi import vim
except ImportError:
    pass


class VMwareHostFactManager(PyVmomi):
    def __init__(self, module):
        super(VMwareHostFactManager, self).__init__(module)
        esxi_host_name = self.params.get('esxi_hostname', None)
        if self.is_vcenter():
            if esxi_host_name is None:
                self.module.fail_json(msg="Connected to a vCenter system without specifying esxi_hostname")
            self.host = self.get_all_host_objs(esxi_host_name=esxi_host_name)
            if len(self.host) > 1:
                self.module.fail_json(msg="esxi_hostname matched multiple hosts")
            self.host = self.host[0]
        else:
            self.host = find_obj(self.content, [vim.HostSystem], None)

        if self.host is None:
            self.module.fail_json(msg="Failed to find host system.")

    def all_facts(self):
        ansible_facts = {}
        ansible_facts.update(self.get_cpu_facts())
        ansible_facts.update(self.get_memory_facts())
        ansible_facts.update(self.get_datastore_facts())
        ansible_facts.update(self.get_network_facts())
        ansible_facts.update(self.get_system_facts())
        ansible_facts.update(self.get_vsan_facts())
        ansible_facts.update(self.get_cluster_facts())
        self.module.exit_json(changed=False, ansible_facts=ansible_facts)

    def get_cluster_facts(self):
        cluster_facts = {'cluster': None}
        if self.host.parent and isinstance(self.host.parent, vim.ClusterComputeResource):
            cluster_facts.update(cluster=self.host.parent.name)
        return cluster_facts

    def get_vsan_facts(self):
        config_mgr = self.host.configManager.vsanSystem
        if config_mgr is None:
            return {
                'vsan_cluster_uuid': None,
                'vsan_node_uuid': None,
                'vsan_health': "unknown",
            }

        status = config_mgr.QueryHostStatus()
        return {
            'vsan_cluster_uuid': status.uuid,
            'vsan_node_uuid': status.nodeUuid,
            'vsan_health': status.health,
        }

    def get_cpu_facts(self):
        return {
            'ansible_processor': self.host.summary.hardware.cpuModel,
            'ansible_processor_cores': self.host.summary.hardware.numCpuCores,
            'ansible_processor_count': self.host.summary.hardware.numCpuPkgs,
            'ansible_processor_vcpus': self.host.summary.hardware.numCpuThreads,
        }

    def get_memory_facts(self):
        return {
            'ansible_memfree_mb': self.host.hardware.memorySize // 1024 // 1024 - self.host.summary.quickStats.overallMemoryUsage,
            'ansible_memtotal_mb': self.host.hardware.memorySize // 1024 // 1024,
        }

    def get_datastore_facts(self):
        facts = dict()
        facts['ansible_datastore'] = []
        for store in self.host.datastore:
            _tmp = {
                'name': store.summary.name,
                'total': bytes_to_human(store.summary.capacity),
                'free': bytes_to_human(store.summary.freeSpace),
            }
            facts['ansible_datastore'].append(_tmp)
        return facts

    def get_network_facts(self):
        facts = dict()
        facts['ansible_interfaces'] = []
        facts['ansible_all_ipv4_addresses'] = []
        for nic in self.host.config.network.vnic:
            device = nic.device
            facts['ansible_interfaces'].append(device)
            facts['ansible_all_ipv4_addresses'].append(nic.spec.ip.ipAddress)
            _tmp = {
                'device': device,
                'ipv4': {
                    'address': nic.spec.ip.ipAddress,
                    'netmask': nic.spec.ip.subnetMask,
                },
                'macaddress': nic.spec.mac,
                'mtu': nic.spec.mtu,
            }
            facts['ansible_' + device] = _tmp
        return facts

    def get_system_facts(self):
        sn = 'NA'
        for info in self.host.hardware.systemInfo.otherIdentifyingInfo:
            if info.identifierType.key == 'ServiceTag':
                sn = info.identifierValue
        facts = {
            'ansible_distribution': self.host.config.product.name,
            'ansible_distribution_version': self.host.config.product.version,
            'ansible_distribution_build': self.host.config.product.build,
            'ansible_os_type': self.host.config.product.osType,
            'ansible_system_vendor': self.host.hardware.systemInfo.vendor,
            'ansible_hostname': self.host.summary.config.name,
            'ansible_product_name': self.host.hardware.systemInfo.model,
            'ansible_product_serial': sn,
            'ansible_bios_date': self.host.hardware.biosInfo.releaseDate,
            'ansible_bios_version': self.host.hardware.biosInfo.biosVersion,
        }
        return facts


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        esxi_hostname=dict(type='str', required=False),
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    vm_host_manager = VMwareHostFactManager(module)
    vm_host_manager.all_facts()


if __name__ == '__main__':
    main()
