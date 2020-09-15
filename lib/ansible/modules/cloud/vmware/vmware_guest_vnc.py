#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018, Armin Ranjbar Daemi <armin@webair.com>
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
module: vmware_guest_vnc
short_description: Manages VNC remote display on virtual machines in vCenter
description:
  - This module can be used to enable and disable VNC remote display on virtual machine.
version_added: 2.8
author:
  - Armin Ranjbar Daemi (@rmin)
requirements:
  - python >= 2.6
  - PyVmomi
options:
  datacenter:
    description:
    - Destination datacenter for the deploy operation.
    - This parameter is case sensitive.
    default: ha-datacenter
    type: str
  state:
    description:
      - Set the state of VNC on virtual machine.
    choices: [present, absent]
    default: present
    required: false
    type: str
  name:
    description:
      - Name of the virtual machine to work with.
      - Virtual machine names in vCenter are not necessarily unique, which may be problematic, see C(name_match).
    required: false
    type: str
  name_match:
    description:
      - If multiple virtual machines matching the name, use the first or last found.
    default: first
    choices: [first, last]
    required: false
    type: str
  uuid:
    description:
      - UUID of the instance to manage if known, this is VMware's unique identifier.
      - This is required, if C(name) or C(moid) is not supplied.
    required: false
    type: str
  moid:
    description:
      - Managed Object ID of the instance to manage if known, this is a unique identifier only within a single vCenter instance.
      - This is required if C(name) or C(uuid) is not supplied.
    version_added: '2.9'
    type: str
  folder:
    description:
      - Destination folder, absolute or relative path to find an existing guest.
      - The folder should include the datacenter. ESX's datacenter is ha-datacenter
    required: false
    type: str
  vnc_ip:
    description:
      - Sets an IP for VNC on virtual machine.
      - This is required only when I(state) is set to present and will be ignored if I(state) is absent.
    default: 0.0.0.0
    required: false
    type: str
  vnc_port:
    description:
      - The port that VNC listens on. Usually a number between 5900 and 7000 depending on your config.
      - This is required only when I(state) is set to present and will be ignored if I(state) is absent.
    default: 0
    required: false
    type: int
  vnc_password:
    description:
      - Sets a password for VNC on virtual machine.
      - This is required only when I(state) is set to present and will be ignored if I(state) is absent.
    default: ""
    required: false
    type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Enable VNC remote display on the VM
  vmware_guest_vnc:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    folder: /mydatacenter/vm
    name: testvm1
    vnc_port: 5990
    vnc_password: vNc5ecr3t
    datacenter: "{{ datacenter_name }}"
    state: present
  delegate_to: localhost
  register: vnc_result

- name: Disable VNC remote display on the VM
  vmware_guest_vnc:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    datacenter: "{{ datacenter_name }}"
    uuid: 32074771-7d6b-699a-66a8-2d9cf8236fff
    state: absent
  delegate_to: localhost
  register: vnc_result

- name: Disable VNC remote display on the VM using MoID
  vmware_guest_vnc:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    datacenter: "{{ datacenter_name }}"
    moid: vm-42
    state: absent
  delegate_to: localhost
  register: vnc_result
'''

RETURN = '''
changed:
  description: If anything changed on VM's extraConfig.
  returned: always
  type: bool
failed:
  description: If changes failed.
  returned: always
  type: bool
instance:
  description: Dictionary describing the VM, including VNC info.
  returned: On success in both I(state)
  type: dict
'''

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, get_vnc_extraconfig, wait_for_task, gather_vm_facts, TaskError
from ansible.module_utils._text import to_native


def set_vnc_extraconfig(content, vm, enabled, ip, port, password):
    result = dict(
        changed=False,
        failed=False,
    )
    # set new values
    key_prefix = "remotedisplay.vnc."
    new_values = dict()
    for key in ['enabled', 'ip', 'port', 'password']:
        new_values[key_prefix + key] = ""
    if enabled:
        new_values[key_prefix + "enabled"] = "true"
        new_values[key_prefix + "password"] = str(password).strip()
        new_values[key_prefix + "ip"] = str(ip).strip()
        new_values[key_prefix + "port"] = str(port).strip()

    # get current vnc config
    current_values = get_vnc_extraconfig(vm)
    # check if any value is changed
    reconfig_vm = False
    for key, val in new_values.items():
        key = key.replace(key_prefix, "")
        current_value = current_values.get(key, "")
        # enabled is not case-sensitive
        if key == "enabled":
            current_value = current_value.lower()
            val = val.lower()
        if current_value != val:
            reconfig_vm = True
    if not reconfig_vm:
        return result
    # reconfigure vm
    spec = vim.vm.ConfigSpec()
    spec.extraConfig = []
    for key, val in new_values.items():
        opt = vim.option.OptionValue()
        opt.key = key
        opt.value = val
        spec.extraConfig.append(opt)
    task = vm.ReconfigVM_Task(spec)
    try:
        wait_for_task(task)
    except TaskError as task_err:
        result['failed'] = True
        result['msg'] = to_native(task_err)

    if task.info.state == 'error':
        result['failed'] = True
        result['msg'] = task.info.error.msg
    else:
        result['changed'] = True
        result['instance'] = gather_vm_facts(content, vm)
    return result


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present', choices=['present', 'absent']),
        name=dict(type='str'),
        name_match=dict(type='str', choices=['first', 'last'], default='first'),
        uuid=dict(type='str'),
        moid=dict(type='str'),
        folder=dict(type='str'),
        vnc_ip=dict(type='str', default='0.0.0.0'),
        vnc_port=dict(type='int', default=0),
        vnc_password=dict(type='str', default='', no_log=True),
        datacenter=dict(type='str', default='ha-datacenter')
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[
            ['name', 'uuid', 'moid']
        ],
        mutually_exclusive=[
            ['name', 'uuid', 'moid']
        ]
    )

    result = dict(changed=False, failed=False)

    pyv = PyVmomi(module)
    vm = pyv.get_vm()
    if vm:
        result = set_vnc_extraconfig(
            pyv.content,
            vm,
            (module.params['state'] == "present"),
            module.params['vnc_ip'],
            module.params['vnc_port'],
            module.params['vnc_password']
        )
    else:
        vm_id = module.params.get('uuid') or module.params.get('name') or module.params.get('moid')
        module.fail_json(msg="Unable to set VNC config for non-existing virtual machine : '%s'" % vm_id)

    if result.get('failed') is True:
        module.fail_json(**result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
