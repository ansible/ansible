#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Wei Gao <gaowei3@qq.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vmware_host_facts
short_description: Gathers facts about remote vmware host
description:
    - Gathers facts about remote vmware host
version_added: 2.5
author:
    - Wei Gao (@woshihaoren)
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

RETURN = '''
instance:
    description: system info about the host machine
    returned: always
    type: dict
    sample: None
'''

from ansible.module_utils.vmware import connect_to_api, vmware_argument_spec, find_obj
from ansible.module_utils.basic import AnsibleModule

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
            'total': sizeof_fmt(store.summary.capacity),
            'free': sizeof_fmt(store.summary.freeSpace)
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
    sn = 'NA'
    for info in host.hardware.systemInfo.otherIdentifyingInfo:
        if info.identifierType.key == 'ServiceTag':
            sn = info.identifierValue
    facts = {
        'ansible_distribution': host.config.product.name,
        'ansible_distribution_version': host.config.product.version,
        'ansible_distribution_build': host.config.product.build,
        'ansible_os_type': host.config.product.osType,
        'ansible_system_vendor': host.hardware.systemInfo.vendor,
        'ansible_hostname': host.summary.config.name,
        'ansible_product_name': host.hardware.systemInfo.model,
        'ansible_product_serial': sn,
        'ansible_bios_date': host.hardware.biosInfo.releaseDate,
        'ansible_bios_version': host.hardware.biosInfo.biosVersion
    }
    return facts


def sizeof_fmt(num):
    """
    Returns the human readable version of a file size

    :param num:
    :return:
    """
    for item in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, item)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


def all_facts(content):
    host = find_obj(content, [vim.HostSystem], None)
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


if __name__ == '__main__':
    main()
