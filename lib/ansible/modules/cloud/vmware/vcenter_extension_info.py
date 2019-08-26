#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
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
module: vcenter_extension_info
short_description: Gather info vCenter extensions
description:
- This module can be used to gather information about vCenter extension.
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
- name: Gather info about vCenter Extensions
  vcenter_extension_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
  register: ext_info
  delegate_to: localhost
'''

RETURN = r'''
extension_info:
    description: List of extensions
    returned: success
    type: list
    sample: [
        {
            "extension_company": "VMware, Inc.",
            "extension_key": "com.vmware.vim.ls",
            "extension_label": "License Services",
            "extension_last_heartbeat_time": "2018-09-03T09:36:18.003768+00:00",
            "extension_subject_name": "",
            "extension_summary": "Provides various license services",
            "extension_type": "",
            "extension_version": "5.0"
        },
        {
            "extension_company": "VMware Inc.",
            "extension_key": "com.vmware.vim.sms",
            "extension_label": "VMware vCenter Storage Monitoring Service",
            "extension_last_heartbeat_time": "2018-09-03T09:36:18.005730+00:00",
            "extension_subject_name": "",
            "extension_summary": "Storage Monitoring and Reporting",
            "extension_type": "",
            "extension_version": "5.5"
        }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi


class VmwareExtManager(PyVmomi):
    def __init__(self, module):
        super(VmwareExtManager, self).__init__(module)

    def gather_plugin_info(self):
        result = dict(changed=False, extension_info=[])
        ext_manager = self.content.extensionManager
        if not ext_manager:
            self.module.exit_json(**result)

        for ext in ext_manager.extensionList:
            ext_info = dict(
                extension_label=ext.description.label,
                extension_summary=ext.description.summary,
                extension_key=ext.key,
                extension_company=ext.company,
                extension_version=ext.version,
                extension_type=ext.type if ext.type else '',
                extension_subject_name=ext.subjectName if ext.subjectName else '',
                extension_last_heartbeat_time=ext.lastHeartbeatTime,
            )
            result['extension_info'].append(ext_info)

        self.module.exit_json(**result)


def main():
    argument_spec = vmware_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    vcenter_extension_info_mgr = VmwareExtManager(module)
    vcenter_extension_info_mgr.gather_plugin_info()


if __name__ == "__main__":
    main()
