#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright, (c) 2019, Ansible Project
# Copyright, (c) 2019, Abhijeet Kasurde <akasurde@redhat.com>
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
module: vmware_guest_extra_config
short_description: Manage extra configuration for the given virtual machine
description:
- This module can be used to update extra configurations for the given virtual machine.
version_added: "2.10"
author:
- Abhijeet Kasurde (@Akasurde)
notes:
- Tested on vSphere 6.5
requirements:
- "python >= 2.7"
- PyVmomi
options:
   name:
     description:
     - Name of the virtual machine to work with.
     required: True
     type: str
   uuid:
     description:
     - UUID of the virtual machine to manage if known. This is VMware's unique identifier.
     - This is a required parameter, if C(name) or C(moid) is not supplied.
     type: str
   moid:
     description:
     - Managed Object ID of the instance to manage if known, this is a unique identifier only within a single vCenter instance.
     - This is a required if C(name) or C(uuid) is not supplied.
     type: str
   state:
     description:
     - The action to take.
     - If set to C(present), then extra configuration is updated.
     - If set to C(absent), then extra configuration is removed.
     default: 'present'
     choices: ['present', 'absent']
     type: str
   use_instance_uuid:
     description:
     - Whether to use the VMWare instance UUID rather than the BIOS UUID.
     default: no
     type: bool
   folder:
     description:
     - Absolute path to find an existing guest.
     - This is a required parameter, if C(name) is supplied and multiple virtual machines with same name are found.
     type: str
   datacenter:
     description:
     - Datacenter name where the virtual machine is located in.
     required: True
     type: str
   config:
     description:
     - A list of names and values of extra configurations that needs to be manage.
     - Value of extra configuration is not required and will be ignored, if C(state) is set to C(absent).
     default: []
     type: list
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Add virtual machine extra config
  vmware_guest_extra_config:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
    state: present
    config:
      - name: pciBridge4.present
        value: True
  delegate_to: localhost
  register: add_extra_config

- name: Remove virtual machine extra config
  vmware_guest_extra_config:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
    state: absent
    config:
      - name: pciBridge4.present
        value: '' # This is ignored since state is absent
  delegate_to: localhost
  register: delete_extra_config

- name: Remove virtual machine extra config using Managed Object ID
  vmware_guest_extra_config:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    moid: vm-42
    state: absent
    config:
      - name: pciBridge4.present
        value: '' # This is ignored since state is absent
  delegate_to: localhost
  register: delete_extra_config
'''

RETURN = """
extra_config_info:
    description: metadata about the virtual machine extra configuration
    returned: always
    type: dict
    sample: {
        "hpet0.present": "TRUE",
        "migrate.hostLog": "VMhost.log",
        "migrate.hostLogState": "none",
        "migrate.migrationId": "0",
        "nvram": "VM_8044.nvram",
        "pciBridge0.present": "TRUE",
        "pciBridge4.functions": "8",
        "pciBridge4.present": "TRUE",
        "pciBridge4.virtualDev": "pcieRootPort",
        "pciBridge5.functions": "8",
        "pciBridge5.present": "TRUE",
        "pciBridge5.virtualDev": "pcieRootPort",
        "pciBridge6.functions": "8",
        "pciBridge6.present": "TRUE",
        "pciBridge6.virtualDev": "pcieRootPort",
        "pciBridge7.functions": "8",
        "pciBridge7.present": "TRUE",
        "pciBridge7.virtualDev": "pcieRootPort",
        "svga.present": "TRUE",
        "vmware.tools.internalversion": "-1",
        "vmware.tools.requiredversion": "10272"
    }
"""

try:
    from pyVmomi import vim, VmomiSupport
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, wait_for_task


class VmExtraConfigManager(PyVmomi):
    def __init__(self, module):
        super(VmExtraConfigManager, self).__init__(module)

    def set_extra_config(self, vm, user_fields=None):
        current_fields = dict()
        changed = False
        failed = False
        vm_extra_config_spec = vim.vm.ConfigSpec()
        vm_extra_config_spec.extraConfig = []

        for option in vm.config.extraConfig:
            current_fields[option.key] = option.value

        for user_defined_option in self.module.params['config']:
            name = user_defined_option['name']
            option = vim.option.OptionValue()
            option.key = name

            if self.module.params['state'] == 'absent':
                # Delete
                option.value = ''
                changed = True
            else:
                value = user_defined_option['value']
                if name in list(current_fields.keys()):
                    # Update
                    if value != current_fields[name]:
                        if value in frozenset(('y', 'yes', 'on', 'true', 't', True)):
                            option.value = 'TRUE'
                        elif value in frozenset(('n', 'no', 'off', 'false', 'f', False)):
                            option.value = 'FALSE'
                        elif self.is_integer(value):
                            option.value = VmomiSupport.vmodlTypes['int'](value)
                        elif self.is_integer(value, 'long'):
                            option.value = VmomiSupport.vmodlTypes['long'](value)
                        else:
                            option.value = value
                        changed = True
                else:
                    # Create
                    if value in frozenset(('y', 'yes', 'on', 'true', 't', True)):
                        option.value = 'TRUE'
                    elif value in frozenset(('n', 'no', 'off', 'false', 'f', False)):
                        option.value = 'FALSE'
                    elif self.is_integer(value):
                        option.value = VmomiSupport.vmodlTypes['int'](value)
                    elif self.is_integer(value, 'long'):
                        option.value = VmomiSupport.vmodlTypes['long'](value)
                    else:
                        option.value = value
                    changed = True
            vm_extra_config_spec.extraConfig.append(option)

        if vm_extra_config_spec.extraConfig and changed:
            if self.module.check_mode:
                self.module.exit_json(changed=True, failed=failed, extra_config_info=current_fields)

            task = vm.ReconfigVM_Task(vm_extra_config_spec)
            try:
                changed, error = wait_for_task(task)
            except Exception as e:
                self.module.fail_json(msg="Failed to reconfigure vm %s while updating extra config: %s" % (vm.name, e))

        for option in vm.config.extraConfig:
            current_fields[option.key] = option.value
        self.module.exit_json(changed=changed, failed=failed, extra_config_info=current_fields)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        datacenter=dict(type='str'),
        name=dict(required=True, type='str'),
        folder=dict(type='str'),
        uuid=dict(type='str'),
        moid=dict(type='str'),
        use_instance_uuid=dict(type='bool', default=False),
        state=dict(type='str', default='present',
                   choices=['absent', 'present']),
        config=dict(
            type='list',
            default=[],
            options=dict(
                name=dict(type='str', required=True),
                value=dict(type='str'),
            )
        ),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[
            ['name', 'uuid', 'moid']
        ],
    )

    if module.params.get('folder'):
        # FindByInventoryPath() does not require an absolute path
        # so we should leave the input folder path unmodified
        module.params['folder'] = module.params['folder'].rstrip('/')

    pyv = VmExtraConfigManager(module)

    # Check if the virtual machine exists before continuing
    vm = pyv.get_vm()

    if vm:
        pyv.set_extra_config(vm)
    # virtual machine does not exists
    vm_id = (module.params.get('name') or module.params.get('uuid') or module.params.get('moid'))
    module.fail_json(msg="Unable to manage extra configuration for non-existing virtual machine %s" % vm_id)


if __name__ == '__main__':
    main()
