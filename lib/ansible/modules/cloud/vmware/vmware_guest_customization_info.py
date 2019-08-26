#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: vmware_guest_customization_info
short_description: Gather info about VM customization specifications
description:
    - This module can be used to gather information about customization specifications.
    - All parameters and VMware object names are case sensitive.
version_added: '2.9'
author:
    - Abhijeet Kasurde (@Akasurde)
notes:
    - Tested on vSphere 6.0 and 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
   spec_name:
     description:
     - Name of customization specification to find.
     required: False
     type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Gather info about all customization specification
  vmware_guest_customization_info:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
  delegate_to: localhost
  register: all_custom_spec_info

- name: Gather info about customization specification with the given name
  vmware_guest_customization_info:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    spec_name: custom_linux_spec
  delegate_to: localhost
  register: custom_spec_info
'''

RETURN = """
custom_spec_info:
    description: metadata about the customization specification
    returned: always
    type: dict
    sample: {
        "assignip-eee0d684-44b7-457c-8c55-2585590b0d99": {
            "change_version": "1523438001",
            "description": "sample description",
            "dns_server_list": [],
            "dns_suffix_list": [],
            "domain": "None",
            "hostname": "sample1",
            "hw_clock_utc": null,
            "last_updated_time": "2018-04-11T09:13:21+00:00",
            "name": "sample",
            "nic_setting_map": [
                {
                    "dns_domain": null,
                    "gateway": [],
                    "ip_address": "192.168.10.10",
                    "net_bios": null,
                    "nic_dns_server_list": [],
                    "primary_wins": null,
                    "secondry_wins": null,
                    "subnet_mask": "255.255.255.0"
                }
            ],
            "time_zone": null,
            "type": "Linux"
        },
    }
"""

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec


class VmwareCustomSpecManger(PyVmomi):
    def __init__(self, module):
        super(VmwareCustomSpecManger, self).__init__(module)
        self.cc_mgr = self.content.customizationSpecManager
        if self.cc_mgr is None:
            self.module.fail_json(msg="Failed to get customization spec manager.")

    def gather_custom_spec_info(self):
        """
        Gather information about customization specifications
        """

        spec_name = self.params.get('spec_name', None)
        specs_list = []
        if spec_name:
            if self.cc_mgr.DoesCustomizationSpecExist(name=spec_name):
                specs_list.append(spec_name)
            else:
                self.module.fail_json(msg="Unable to find customization specification named '%s'" % spec_name)
        else:
            available_specs = self.cc_mgr.info
            for spec_info in available_specs:
                specs_list.append(spec_info.name)

        spec_info = dict()
        for spec in specs_list:
            current_spec = self.cc_mgr.GetCustomizationSpec(name=spec)
            adapter_mapping_list = []
            for nic in current_spec.spec.nicSettingMap:
                temp_data = dict(
                    mac_address=nic.macAddress,
                    ip_address=nic.adapter.ip.ipAddress,
                    subnet_mask=nic.adapter.subnetMask,
                    gateway=[gw for gw in nic.adapter.gateway],
                    nic_dns_server_list=[ndsl for ndsl in nic.adapter.dnsServerList],
                    dns_domain=nic.adapter.dnsDomain,
                    primary_wins=nic.adapter.primaryWINS,
                    secondry_wins=nic.adapter.secondaryWINS,
                    net_bios=nic.adapter.netBIOS,
                )
                adapter_mapping_list.append(temp_data)

            current_hostname = None
            if isinstance(current_spec.spec.identity.hostName, vim.vm.customization.PrefixNameGenerator):
                current_hostname = current_spec.spec.identity.hostName.base
            elif isinstance(current_spec.spec.identity.hostName, vim.vm.customization.FixedName):
                current_hostname = current_spec.spec.identity.hostName.name

            spec_info[spec] = dict(
                # Spec
                name=current_spec.info.name,
                description=current_spec.info.description,
                type=current_spec.info.type,
                last_updated_time=current_spec.info.lastUpdateTime,
                change_version=current_spec.info.changeVersion,
                # Identity
                hostname=current_hostname,
                domain=current_spec.spec.identity.domain,
                time_zone=current_spec.spec.identity.timeZone,
                hw_clock_utc=current_spec.spec.identity.hwClockUTC,
                # global IP Settings
                dns_suffix_list=[i for i in current_spec.spec.globalIPSettings.dnsSuffixList],
                dns_server_list=[i for i in current_spec.spec.globalIPSettings.dnsServerList],
                # NIC setting map
                nic_setting_map=adapter_mapping_list,
            )
        return spec_info


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        spec_name=dict(type='str'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    pyv = VmwareCustomSpecManger(module)
    try:
        module.exit_json(custom_spec_info=pyv.gather_custom_spec_info())
    except Exception as exc:
        module.fail_json(msg="Failed to gather information with exception : %s" % to_text(exc))


if __name__ == '__main__':
    main()
