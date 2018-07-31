#!/usr/bin/python
# -*- coding: utf-8 -*-

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


DOCUMENTATION = '''
---
module: vmware_guest_custom_attribute_def_facts
short_description: Gather facts about custom attributes definitions
description:
    - This module can be used to gather facts about custom attributes definitions.
version_added: 2.7
author:
    - Jimmy Conner
    - Abhijeet Kasurde (@Akasurde)
notes:
    - Tested on vSphere 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: List VMWare Attribute Definitions
  vmware_guest_custom_attribute_def_facts:
    hostname: "{{ vcenter_server }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
  delegate_to: localhost
  register: defs
'''

RETURN = """
custom_attribute_def_facts:
    description: list of all current attribute definitions
    returned: always
    type: list
    sample: ["sample_5", "sample_4"]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec

try:
    from pyVmomi import vim
except ImportError:
    pass


class VmAttributeDefFactManager(PyVmomi):
    def __init__(self, module):
        super(VmAttributeDefFactManager, self).__init__(module)
        self.custom_field_mgr = self.content.customFieldsManager.field

    def gather_def_facts(self):
        return {
            'changed': False,
            'failed': False,
            'custom_attribute_def_facts': [x.name for x in self.custom_field_mgr]
        }


def main():
    argument_spec = vmware_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    pyv = VmAttributeDefFactManager(module)
    results = pyv.gather_def_facts()
    module.exit_json(**results)


if __name__ == '__main__':
    main()
