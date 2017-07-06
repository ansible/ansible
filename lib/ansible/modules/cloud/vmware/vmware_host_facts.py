#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Wei Gao <gaowei3@qq.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vmware_host_facts
short_description: Gathers facts about remote vmware host
description:
    - Gathers facts about remote vmware host
version_added: 2.3
author:
    - Wei Gao
notes:
    - Tested on vSphere 5.5
requirements:
    - "python >= 2.6"
    - PyVmomi
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Gather vmware host facts
  local_action:
    module: vmware_host_facts
    hostname: esxi_ip_or_hostname
    username: username
    password: password
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


def get_cpu_facts(host):
    facts = {
        'ansible_processor': host.summary.hardware.cpuModel, 
        'ansible_processor_cores': host.summary.hardware.numCpuCores, 
        'ansible_processor_count': host.summary.hardware.numCpuPkgs, 
        'ansible_processor_vcpus': host.summary.hardware.numCpuThreads
    }
    return facts
    

def get_memory_facts(host):
    facts = {
        'ansible_memfree_mb': host.hardware.memorySize // 1024 // 1024 - host.summary.quickStats.overallMemoryUsage, 
        'ansible_memtotal_mb': host.hardware.memorySize // 1024 // 1024, 
    }
    return facts


def get_datastore_facts(host):
    facts = {}
    facts['ansible_datastore'] = []
    for store in host.datastore:
        _tmp = {
            'name': store.summary.name,
            'total': store.summary.capacity,
            'free': store.summary.freeSpace
        }
        facts['ansible_datastore'].append(_tmp)
    return facts


def get_network_facts(host):
    facts = {}
    facts['ansible_interfaces'] = []
    facts['ansible_all_ipv4_addresses'] = []
    for nic in host.config.network.vnic:
        device = nic.device
        facts['ansible_interfaces'].append(device)
        facts['ansible_all_ipv4_addresses'].append(nic.spec.ip.ipAddress)
        _tmp = {
            'device': device,
            'ipv4': {
                 'address': nic.spec.ip.ipAddress,
                 'netmask': nic.spec.ip.subnetMask
             },
            'macaddress': nic.spec.mac,
            'mtu': nic.spec.mtu
        }
        facts['ansible_' + device] = _tmp
    return facts


def get_system_facts(host):
    facts = {
        'ansible_distribution': host.config.product.name, 
        'ansible_distribution_version': host.config.product.version, 
        'ansible_os_type': host.config.product.osType, 
        'ansible_system_vendor': host.hardware.systemInfo.vendor,
        'ansible_system_model': host.hardware.systemInfo.model,
        'ansible_bios_date': host.hardware.biosInfo.releaseDate,
        'ansible_bios_version': host.hardware.biosInfo.biosVersion
    }
    return facts


def get_obj(content, vimtype, name=None):
    """
    Return an object by name, if name is None the
    first found object is returned
    """
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if name:
            if c.name == name:
                obj = c
                break
        else:
            obj = c
            break

    container.Destroy()
    return obj


def all_facts(content):
    host = get_obj(content, [vim.HostSystem])
    ansible_facts = {}
    ansible_facts.update(get_cpu_facts(host))
    ansible_facts.update(get_memory_facts(host))
    ansible_facts.update(get_datastore_facts(host))
    ansible_facts.update(get_network_facts(host))
    ansible_facts.update(get_system_facts(host))
    return ansible_facts


def main():

    argument_spec = vmware_argument_spec()
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    try:
        content = connect_to_api(module)
        data = all_facts(content)
        module.exit_json(changed=False, ansible_facts=data)
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)
    except Exception as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.vmware import *
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
