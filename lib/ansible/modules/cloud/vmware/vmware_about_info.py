#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
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
module: vmware_about_info
short_description: Provides information about VMware server to which user is connecting to
description:
- This module can be used to gather information about VMware server to which user is trying to connect.
version_added: '2.9'
author:
- Abhijeet Kasurde (@Akasurde)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Provide information about vCenter
  vmware_about_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
  delegate_to: localhost
  register: vcenter_about_info

- name: Provide information about a standalone ESXi server
  vmware_about_info:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
  delegate_to: localhost
  register: esxi_about_info
'''

RETURN = r'''
about_info:
    description:
    - dict about VMware server
    returned: success
    type: str
    sample:
        {
            "api_type": "VirtualCenter",
            "api_version": "6.5",
            "build": "5973321",
            "instance_uuid": "dbed6e0c-bd88-4ef6-b594-21283e1c677f",
            "license_product_name": "VMware VirtualCenter Server",
            "license_product_version": "6.0",
            "locale_build": "000",
            "locale_version": "INTL",
            "os_type": "darwin-amd64",
            "product_full_name": "VMware vCenter Server 6.5.0 build-5973321",
            "product_line_id": "vpx",
            "product_name": "VMware vCenter Server (govmomi simulator)",
            "vendor": "VMware, Inc.",
            "version": "6.5.0"
        }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi


class VmwareAboutManager(PyVmomi):
    def __init__(self, module):
        super(VmwareAboutManager, self).__init__(module)

    def gather_about_info(self):

        if not self.content:
            self.module.exit_json(changed=False, about_info=dict())

        about = self.content.about

        self.module.exit_json(
            changed=False,
            about_info=dict(
                product_name=about.name,
                product_full_name=about.fullName,
                vendor=about.vendor,
                version=about.version,
                build=about.build,
                locale_version=about.localeVersion,
                locale_build=about.localeBuild,
                os_type=about.osType,
                product_line_id=about.productLineId,
                api_type=about.apiType,
                api_version=about.apiVersion,
                instance_uuid=about.instanceUuid,
                license_product_name=about.licenseProductName,
                license_product_version=about.licenseProductVersion,
            )
        )


def main():
    argument_spec = vmware_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    vmware_about_info_mgr = VmwareAboutManager(module)
    vmware_about_info_mgr.gather_about_info()


if __name__ == "__main__":
    main()
