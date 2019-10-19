#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = r"""
---
module: vmware_host_sriov
short_description: Manage SR-IOV settings on host
description:
- This module can be used to configure, enable/disable SR-IOV functions an ESXi host.
- module didn't reboot host after changes, but put in output "rebootRequired" key.
- User can specify an ESXi hostname or Cluster name. In case of cluster name, all ESXi hosts are updated.
version_added: 2.10
author:
- Viktor Tsymbalyuk (@victron)
notes:
- Tested on vSphere 6.0
requirements:
- python >= 2.7
- PyVmomi
options:
  esxi_hostname:
    description:
    - Name of the host system to work with.
    - This parameter is required if C(cluster_name) is not specified.
    type: str
  cluster_name:
    description:
    - Name of the cluster from which all host systems will be used.
    - This parameter is required if C(esxi_hostname) is not specified.
    type: str
  vmnic:
    description:
    - interface name, like vmnic0
    type: str
    required: True
  sriovOn:
    description:
    - Desired SR-IOV state on interface.
    type: bool
    required: True
  numVirtFunc:
    description:
    - number of functions to activate on interface.
    - if sriovOn false should be equal 0
    - if sriovOn true should be more then 0
    type: int
    required: True
extends_documentation_fragment: vmware.documentation
"""

EXAMPLES = r"""
- name: enable SR-IOV on vmnic0 with 8 functions
  vmware_host_sriov:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    esxi_hostname: "{{ esxi1 }}"
    validate_certs: no
    vmnic: vmnic0
    sriovOn: true
    numVirtFunc: 8

- name: enable SR-IOV on already enabled interface vmnic0
  vmware_host_sriov:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    esxi_hostname: "{{ esxi1 }}"
    validate_certs: no
    vmnic: vmnic0
    sriovOn: true
    numVirtFunc: 8

- name: enable SR-IOV on vmnic0 with big num. of functions
  vmware_host_sriov:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    esxi_hostname: "{{ esxi1 }}"
    validate_certs: no
    vmnic: vmnic0
    sriovOn: true
    numVirtFunc: 100
  ignore_errors: yes

- name: disable SR-IOV on vmnic0
  vmware_host_sriov:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    esxi_hostname: "{{ esxi1 }}"
    validate_certs: no
    vmnic: vmnic0
    sriovOn: false
    numVirtFunc: 0
"""

RETURN = r"""
host_sriov_diff:
    description:
    - contains info about SR-IOV staus on vmnic before, after and requested changes
    - sometimes vCenter slowly update info, as result "after" contains same info as "before"
      need to run again in check_mode or reboot host, as ESXi requested
    returned: always
    type: dict
    "sample": {
        "changed": true,
        "diff": {
            "after": {
                "host_test": {
                    "sriovActive": false,
                    "sriovEnabled": true,
                    "maxVirtualFunctionSupported": 63,
                    "numVirtualFunction": 0,
                    "numVirtualFunctionRequested": 8,
                    "rebootRequired": true,
                    "sriovCapable": true
                }
            },
            "before": {
                "host_test": {
                    "sriovActive": false,
                    "sriovEnabled": false,
                    "maxVirtualFunctionSupported": 63,
                    "numVirtualFunction": 0,
                    "numVirtualFunctionRequested": 0,
                    "rebootRequired": false,
                    "sriovCapable": true
                }
            },
            "changes": {
                "host_test": {
                    "numVirtualFunction": 8,
                    "rebootRequired": true,
                    "sriovEnabled": true
                }
            }
        }
    }
"""


try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi
from ansible.module_utils._text import to_native
from time import sleep


class VmwareAdapterConfigManager(PyVmomi):
    """Class to configure SR-IOV settings"""

    def __init__(self, module):
        super(VmwareAdapterConfigManager, self).__init__(module)
        cluster_name = self.params.get("cluster_name", None)
        esxi_host_name = self.params.get("esxi_hostname", None)

        self.vmnic = self.params.get("vmnic", None)
        self.sriovOn = self.params.get("sriovOn", None)
        self.numVirtFunc = self.params.get("numVirtFunc", None)

        self.hosts = self.get_all_host_objs(
            cluster_name=cluster_name, esxi_host_name=esxi_host_name
        )
        if not self.hosts:
            self.module.fail_json(msg="Failed to find host system.")
        # self.change_list = []
        self.results = {"before": {}, "after": {}, "changes": {}}

    def set_host_state(self):
        """Check ESXi host configuration"""
        change_list = []
        changed = False
        for host in self.hosts:
            self.results["before"][host.name] = {}
            self.results["after"][host.name] = {}
            self.results["changes"][host.name] = {}
            self.results["before"][host.name] = self._check_sriov(host)
            self.results["changes"][host.name]["rebootRequired"] = self.results[
                "before"
            ][host.name]["rebootRequired"]

            # check compatability
            if not self.results["before"][host.name]["sriovCapable"]:
                change_list.append(False)
                self.results["changes"][host.name][
                    "msg"
                ] = "sriov not supported on host= %s, nic= %s" % (host.name, self.vmnic)
                self.results["after"][host.name] = self._check_sriov(host)
                continue

            if (
                self.results["before"][host.name]["maxVirtualFunctionSupported"]
                < self.numVirtFunc
            ):
                change_list.append(False)
                maxVirtualFun = self.results["before"][host.name][
                    "maxVirtualFunctionSupported"
                ]
                self.results["changes"][host.name]["msg"] = (
                    "maxVirtualFunctionSupported= %d on %s"
                    % (maxVirtualFun, self.vmnic)
                )
                self.results["after"][host.name] = self._check_sriov(host)
                continue

            # check current settings
            params_to_change = {"sriovEnabled": None, "numVirtualFunction": None}
            if self.results["before"][host.name]["sriovEnabled"] != self.sriovOn:
                params_to_change["sriovEnabled"] = self.sriovOn

            if (
                self.results["before"][host.name]["numVirtualFunction"]
                != self.numVirtFunc
            ):
                params_to_change["numVirtualFunction"] = self.numVirtFunc

            success = self._update_sriov(host, **params_to_change)
            if success:
                change_list.append(True)
            else:
                change_list.append(False)

            self.results["after"][host.name] = self._check_sriov(host)
            self.results["changes"][host.name]["rebootRequired"] = self.results[
                "after"
            ][host.name]["rebootRequired"]

        if any(change_list):
            changed = True
        self.module.exit_json(changed=changed, diff=self.results)

    def _check_sriov(self, host):
        pnic_info = {}
        pnic_info["rebootRequired"] = host.summary.rebootRequired
        for pci_device in host.configManager.pciPassthruSystem.pciPassthruInfo:
            if pci_device.id == self._getPciId(host):
                try:
                    if pci_device.sriovCapable:
                        pnic_info["sriovCapable"] = True
                        pnic_info["sriovEnabled"] = pci_device.sriovEnabled
                        pnic_info["sriovActive"] = pci_device.sriovActive
                        pnic_info["numVirtualFunction"] = pci_device.numVirtualFunction
                        pnic_info[
                            "numVirtualFunctionRequested"
                        ] = pci_device.numVirtualFunctionRequested
                        pnic_info[
                            "maxVirtualFunctionSupported"
                        ] = pci_device.maxVirtualFunctionSupported
                    else:
                        pnic_info["sriovCapable"] = False
                except AttributeError:
                    pnic_info["sriovCapable"] = False
                break
        return pnic_info

    def _getPciId(self, host):
        for pnic in host.config.network.pnic:
            if pnic.device == self.vmnic:
                return pnic.pci
        self.module.fail_json(msg="No nic= %s on host= %s" % (self.vmnic, host.name))

    def _update_sriov(self, host, sriovEnabled=None, numVirtualFunction=None):
        if sriovEnabled is None and numVirtualFunction is None:
            self.results["changes"][host.name][
                "msg"
            ] = "No any changes, already configured"
            return False
        nic_sriov = vim.host.SriovConfig()
        nic_sriov.id = self._getPciId(host)
        if sriovEnabled is not None:
            nic_sriov.sriovEnabled = sriovEnabled
            self.results["changes"][host.name]["sriovEnabled"] = sriovEnabled
        if numVirtualFunction is not None and numVirtualFunction >= 0:
            nic_sriov.numVirtualFunction = numVirtualFunction
            self.results["changes"][host.name][
                "numVirtualFunction"
            ] = numVirtualFunction

        try:
            if not self.module.check_mode:
                host.configManager.pciPassthruSystem.UpdatePassthruConfig([nic_sriov])
                # looks only for refresh info
                host.configManager.pciPassthruSystem.Refresh()
                sleep(2)  # TODO: needed method to know that host updated info
                return True
            return False
        except vim.fault.HostConfigFault as config_fault:
            self.module.fail_json(
                msg="Failed to configure SR-IOV for host= %s due to : %s"
                % (host.name, to_native(config_fault.msg))
            )
            return False


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        cluster_name=dict(type="str", required=False),
        esxi_hostname=dict(type="str", required=False),
        vmnic=dict(type="str", required=True),
        sriovOn=dict(type="bool", required=True),
        numVirtFunc=dict(type="int", required=True),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[["cluster_name", "esxi_hostname"], ["sriovOn", "numVirtFunc"]],
        supports_check_mode=True,
    )

    vmware_host_adapter_config = VmwareAdapterConfigManager(module)
    vmware_host_adapter_config.set_host_state()


if __name__ == "__main__":
    main()
