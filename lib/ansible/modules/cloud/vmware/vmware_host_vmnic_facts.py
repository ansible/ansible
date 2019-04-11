#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# Copyright: (c) 2018, Christian Kotte <christian.kotte@gmx.de>
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
module: vmware_host_vmnic_facts
short_description: Gathers facts about vmnics available on the given ESXi host
description:
- This module can be used to gather facts about vmnics available on the given ESXi host.
- If C(cluster_name) is provided, then vmnic facts about all hosts from given cluster will be returned.
- If C(esxi_hostname) is provided, then vmnic facts about given host system will be returned.
- Additional details about vswitch and dvswitch with respective vmnic is also provided which is added in 2.7 version.
version_added: '2.5'
author:
- Abhijeet Kasurde (@Akasurde)
- Christian Kotte (@ckotte)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
  capabilities:
    description:
    - Gather facts about general capabilities (Auto negotioation, Wake On LAN, and Network I/O Control).
    type: bool
    default: false
    version_added: 2.8
  directpath_io:
    description:
    - Gather facts about DirectPath I/O capabilites and configuration.
    type: bool
    default: false
    version_added: 2.8
  sriov:
    description:
    - Gather facts about SR-IOV capabilites and configuration.
    type: bool
    default: false
    version_added: 2.8
  esxi_hostname:
    description:
    - Name of the host system to work with.
    - Vmnic facts about this ESXi server will be returned.
    - This parameter is required if C(cluster_name) is not specified.
    type: str
  cluster_name:
    description:
    - Name of the cluster from which all host systems will be used.
    - Vmnic facts about each ESXi server will be returned for the given cluster.
    - This parameter is required if C(esxi_hostname) is not specified.
    type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Gather facts about vmnics of all ESXi Host in the given Cluster
  vmware_host_vmnic_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: '{{ cluster_name }}'
  delegate_to: localhost
  register: cluster_host_vmnics

- name: Gather facts about vmnics of an ESXi Host
  vmware_host_vmnic_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
  delegate_to: localhost
  register: host_vmnics
'''

RETURN = r'''
hosts_vmnics_facts:
    description:
    - dict with hostname as key and dict with vmnics facts as value.
    - for C(num_vmnics), only NICs starting with vmnic are counted. NICs like vusb* are not counted.
    - details about vswitch and dvswitch was added in version 2.7.
    - details about vmnics was added in version 2.8.
    returned: hosts_vmnics_facts
    type: dict
    sample:
        {
            "10.76.33.204": {
                "all": [
                    "vmnic0",
                    "vmnic1"
                ],
                "available": [],
                "dvswitch": {
                    "dvs_0002": [
                        "vmnic1"
                    ]
                },
                "num_vmnics": 2,
                "used": [
                    "vmnic1",
                    "vmnic0"
                ],
                "vmnic_details": [
                    {
                        "actual_duplex": "Full Duplex",
                        "actual_speed": 10000,
                        "adapter": "Intel(R) 82599 10 Gigabit Dual Port Network Connection",
                        "configured_duplex": "Auto negotiate",
                        "configured_speed": "Auto negotiate",
                        "device": "vmnic0",
                        "driver": "ixgbe",
                        "location": "0000:01:00.0",
                        "mac": "aa:bb:cc:dd:ee:ff",
                        "status": "Connected",
                    },
                    {
                        "actual_duplex": "Full Duplex",
                        "actual_speed": 10000,
                        "adapter": "Intel(R) 82599 10 Gigabit Dual Port Network Connection",
                        "configured_duplex": "Auto negotiate",
                        "configured_speed": "Auto negotiate",
                        "device": "vmnic1",
                        "driver": "ixgbe",
                        "location": "0000:01:00.1",
                        "mac": "ab:ba:cc:dd:ee:ff",
                        "status": "Connected",
                    },
                ],
                "vswitch": {
                    "vSwitch0": [
                        "vmnic0"
                    ]
                }
            }
        }
'''

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi, get_all_objs


class HostVmnicMgr(PyVmomi):
    """Class to manage vmnic facts"""
    def __init__(self, module):
        super(HostVmnicMgr, self).__init__(module)
        self.capabilities = self.params.get('capabilities')
        self.directpath_io = self.params.get('directpath_io')
        self.sriov = self.params.get('sriov')
        cluster_name = self.params.get('cluster_name', None)
        esxi_host_name = self.params.get('esxi_hostname', None)
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)
        if not self.hosts:
            self.module.fail_json(msg="Failed to find host system.")

    def find_dvs_by_uuid(self, uuid=None):
        """Find DVS by it's UUID"""
        dvs_obj = None
        if uuid is None:
            return dvs_obj

        dvswitches = get_all_objs(self.content, [vim.DistributedVirtualSwitch])
        for dvs in dvswitches:
            if dvs.uuid == uuid:
                dvs_obj = dvs
                break

        return dvs_obj

    def gather_host_vmnic_facts(self):
        """Gather vmnic facts"""
        hosts_vmnic_facts = {}
        for host in self.hosts:
            host_vmnic_facts = dict(all=[], available=[], used=[], vswitch=dict(), dvswitch=dict())
            host_nw_system = host.configManager.networkSystem
            if host_nw_system:
                nw_config = host_nw_system.networkConfig
                vmnics = [pnic.device for pnic in nw_config.pnic if pnic.device.startswith('vmnic')]
                host_vmnic_facts['all'] = [pnic.device for pnic in nw_config.pnic]
                host_vmnic_facts['num_vmnics'] = len(vmnics)
                host_vmnic_facts['vmnic_details'] = []
                for pnic in host.config.network.pnic:
                    pnic_facts = dict()
                    if pnic.device.startswith('vmnic'):
                        if pnic.pci:
                            pnic_facts['location'] = pnic.pci
                            for pci_device in host.hardware.pciDevice:
                                if pci_device.id == pnic.pci:
                                    pnic_facts['adapter'] = pci_device.vendorName + ' ' + pci_device.deviceName
                                    break
                        else:
                            pnic_facts['location'] = 'PCI'
                        pnic_facts['device'] = pnic.device
                        pnic_facts['driver'] = pnic.driver
                        if pnic.linkSpeed:
                            pnic_facts['status'] = 'Connected'
                            pnic_facts['actual_speed'] = pnic.linkSpeed.speedMb
                            pnic_facts['actual_duplex'] = 'Full Duplex' if pnic.linkSpeed.duplex else 'Half Duplex'
                        else:
                            pnic_facts['status'] = 'Disconnected'
                            pnic_facts['actual_speed'] = 'N/A'
                            pnic_facts['actual_duplex'] = 'N/A'
                        if pnic.spec.linkSpeed:
                            pnic_facts['configured_speed'] = pnic.spec.linkSpeed.speedMb
                            pnic_facts['configured_duplex'] = 'Full Duplex' if pnic.spec.linkSpeed.duplex else 'Half Duplex'
                        else:
                            pnic_facts['configured_speed'] = 'Auto negotiate'
                            pnic_facts['configured_duplex'] = 'Auto negotiate'
                        pnic_facts['mac'] = pnic.mac
                        # General NIC capabilities
                        if self.capabilities:
                            pnic_facts['nioc_status'] = 'Allowed' if pnic.resourcePoolSchedulerAllowed else 'Not allowed'
                            pnic_facts['auto_negotiation_supported'] = pnic.autoNegotiateSupported
                            pnic_facts['wake_on_lan_supported'] = pnic.wakeOnLanSupported
                        # DirectPath I/O and SR-IOV capabilities and configuration
                        if self.directpath_io:
                            pnic_facts['directpath_io_supported'] = pnic.vmDirectPathGen2Supported
                        if self.directpath_io or self.sriov:
                            if pnic.pci:
                                for pci_device in host.configManager.pciPassthruSystem.pciPassthruInfo:
                                    if pci_device.id == pnic.pci:
                                        if self.directpath_io:
                                            pnic_facts['passthru_enabled'] = pci_device.passthruEnabled
                                            pnic_facts['passthru_capable'] = pci_device.passthruCapable
                                            pnic_facts['passthru_active'] = pci_device.passthruActive
                                        if self.sriov:
                                            try:
                                                if pci_device.sriovCapable:
                                                    pnic_facts['sriov_status'] = (
                                                        'Enabled' if pci_device.sriovEnabled else 'Disabled'
                                                    )
                                                    pnic_facts['sriov_active'] = \
                                                        pci_device.sriovActive
                                                    pnic_facts['sriov_virt_functions'] = \
                                                        pci_device.numVirtualFunction
                                                    pnic_facts['sriov_virt_functions_requested'] = \
                                                        pci_device.numVirtualFunctionRequested
                                                    pnic_facts['sriov_virt_functions_supported'] = \
                                                        pci_device.maxVirtualFunctionSupported
                                                else:
                                                    pnic_facts['sriov_status'] = 'Not supported'
                                            except AttributeError:
                                                pnic_facts['sriov_status'] = 'Not supported'
                        host_vmnic_facts['vmnic_details'].append(pnic_facts)

                vswitch_vmnics = []
                proxy_switch_vmnics = []
                if nw_config.vswitch:
                    for vswitch in nw_config.vswitch:
                        host_vmnic_facts['vswitch'][vswitch.name] = []
                        # Workaround for "AttributeError: 'NoneType' object has no attribute 'nicDevice'"
                        # this issue doesn't happen every time; vswitch.spec.bridge.nicDevice exists!
                        try:
                            for vnic in vswitch.spec.bridge.nicDevice:
                                vswitch_vmnics.append(vnic)
                                host_vmnic_facts['vswitch'][vswitch.name].append(vnic)
                        except AttributeError:
                            pass

                if nw_config.proxySwitch:
                    for proxy_config in nw_config.proxySwitch:
                        dvs_obj = self.find_dvs_by_uuid(uuid=proxy_config.uuid)
                        if dvs_obj:
                            host_vmnic_facts['dvswitch'][dvs_obj.name] = []
                        for proxy_nic in proxy_config.spec.backing.pnicSpec:
                            proxy_switch_vmnics.append(proxy_nic.pnicDevice)
                            if dvs_obj:
                                host_vmnic_facts['dvswitch'][dvs_obj.name].append(proxy_nic.pnicDevice)

                used_vmics = proxy_switch_vmnics + vswitch_vmnics
                host_vmnic_facts['used'] = used_vmics
                host_vmnic_facts['available'] = [pnic.device for pnic in nw_config.pnic if pnic.device not in used_vmics]

            hosts_vmnic_facts[host.name] = host_vmnic_facts
        return hosts_vmnic_facts


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        cluster_name=dict(type='str', required=False),
        esxi_hostname=dict(type='str', required=False),
        capabilities=dict(type='bool', required=False, default=False),
        directpath_io=dict(type='bool', required=False, default=False),
        sriov=dict(type='bool', required=False, default=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['cluster_name', 'esxi_hostname'],
        ],
        supports_check_mode=True,
    )

    host_vmnic_mgr = HostVmnicMgr(module)
    module.exit_json(changed=False, hosts_vmnics_facts=host_vmnic_mgr.gather_host_vmnic_facts())


if __name__ == "__main__":
    main()
