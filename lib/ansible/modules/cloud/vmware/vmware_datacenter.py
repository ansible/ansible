#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2018, Ansible Project
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
module: vmware_datacenter
short_description: Manage VMware vSphere Datacenters
description:
    - This module can be used to manage (create, delete) VMware vSphere Datacenters.
version_added: 2.0
author:
- Joseph Callen (@jcpowermac)
- Kamil Szczygiel (@kamsz)
notes:
    - Tested on vSphere 6.0, 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    datacenter_name:
      description:
      - The name of the datacenter the cluster will be created in.
      required: True
      type: str
    state:
      description:
      - If the datacenter should be present or absent.
      choices: [ present, absent ]
      default: present
      type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Create Datacenter
  vmware_datacenter:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: '{{ datacenter_name }}'
    state: present
  delegate_to: localhost

- name: Delete Datacenter
  vmware_datacenter:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: '{{ datacenter_name }}'
    state: absent
  delegate_to: localhost
  register: datacenter_delete_result
'''

RETURN = """#
"""

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, find_datacenter_by_name, vmware_argument_spec, wait_for_task
from ansible.module_utils._text import to_native


class VmwareDatacenterManager(PyVmomi):
    def __init__(self, module):
        super(VmwareDatacenterManager, self).__init__(module)
        self.datacenter_name = self.params.get('datacenter_name')
        self.datacenter_obj = self.get_datacenter()

    def ensure(self):
        state = self.module.params.get('state')

        if state == 'present':
            self.create_datacenter()

        if state == 'absent':
            self.destroy_datacenter()

    def get_datacenter(self):
        try:
            datacenter_obj = find_datacenter_by_name(self.content, self.datacenter_name)
            return datacenter_obj
        except (vmodl.MethodFault, vmodl.RuntimeFault) as runtime_fault:
            self.module.fail_json(msg="Failed to get datacenter '%s'"
                                      " due to : %s" % (self.datacenter_name,
                                                        to_native(runtime_fault.msg)))
        except Exception as generic_exc:
            self.module.fail_json(msg="Failed to get datacenter"
                                      " '%s' due to generic error: %s" % (self.datacenter_name,
                                                                          to_native(generic_exc)))

    def create_datacenter(self):
        folder = self.content.rootFolder
        changed = False
        try:
            if not self.datacenter_obj and not self.module.check_mode:
                changed = True
                folder.CreateDatacenter(name=self.datacenter_name)
            self.module.exit_json(changed=changed)
        except vim.fault.DuplicateName as duplicate_name:
            self.module.exit_json(changed=changed)
        except vim.fault.InvalidName as invalid_name:
            self.module.fail_json(msg="Specified datacenter name '%s' is an"
                                      " invalid name : %s" % (self.datacenter_name,
                                                              to_native(invalid_name.msg)))
        except vmodl.fault.NotSupported as not_supported:
            # This should never happen
            self.module.fail_json(msg="Trying to create a datacenter '%s' on"
                                      " an incorrect folder object : %s" % (self.datacenter_name,
                                                                            to_native(not_supported.msg)))
        except (vmodl.RuntimeFault, vmodl.MethodFault) as runtime_fault:
            self.module.fail_json(msg="Failed to create a datacenter"
                                      " '%s' due to : %s" % (self.datacenter_name,
                                                             to_native(runtime_fault.msg)))
        except Exception as generic_exc:
            self.module.fail_json(msg="Failed to create a datacenter"
                                      " '%s' due to generic error: %s" % (self.datacenter_name,
                                                                          to_native(generic_exc)))

    def destroy_datacenter(self):
        results = dict(changed=False)
        try:
            if self.datacenter_obj and not self.module.check_mode:
                task = self.datacenter_obj.Destroy_Task()
                changed, result = wait_for_task(task)
                results['changed'] = changed
                results['result'] = result
            self.module.exit_json(**results)
        except (vim.fault.VimFault, vmodl.RuntimeFault, vmodl.MethodFault) as runtime_fault:
            self.module.fail_json(msg="Failed to delete a datacenter"
                                      " '%s' due to : %s" % (self.datacenter_name,
                                                             to_native(runtime_fault.msg)))
        except Exception as generic_exc:
            self.module.fail_json(msg="Failed to delete a datacenter"
                                      " '%s' due to generic error: %s" % (self.datacenter_name,
                                                                          to_native(generic_exc)))


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            datacenter_name=dict(required=True, type='str'),
            state=dict(default='present', choices=['present', 'absent'], type='str')
        )
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    vmware_datacenter_mgr = VmwareDatacenterManager(module)
    vmware_datacenter_mgr.ensure()


if __name__ == '__main__':
    main()
