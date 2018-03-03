#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2018, Armin Ranjbar Daemi randjbar@gmail.com
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vmware_guest_vnc

short_description: Manages VNC remote display on virtual machines in vCenter

description:
  - Enables and disables VNC remote display on virtual machine.

version_added: '2.6'

author:
  - Armin Ranjbar Daemi (@rmin) <randjbar@gmail.com>

requirements:
  - python >= 2.6
  - PyVmomi

options:
  hostname:
    description:
      - vSphere or VCenter hostname.
    required: true
  username:
    description:
      - vSphere or VCenter username.
    required: true
  password:
    description:
      - vSphere or VCenter password.
    required: true
  port:
    description:
      - vSphere or VCenter port.
    required: false
    default: 443
  validate_certs:
    description:
      - Validate SSL certs when connecting to host.
    choices:
      - true
      - false
    default: true
    required: false
    type: bool
  state:
    description:
      - Set the state of VNC on virtual machine.
    choices:
      - present
      - absent
    default: present
    required: false
  name:
    description:
      - Name of the virtual machine to work with.
      - Virtual machine names in vCenter are not necessarily unique, which may be problematic, see C(name_match).
    required: false
  name_match:
    description:
      - If multiple virtual machines matching the name, use the first or last found.
    default: first
    choices:
      - first
      - last
    required: false
  uuid:
    description:
      - UUID of the instance to manage if known, this is VMware's unique identifier.
      - This is required if name is not supplied.
    required: false
  folder:
    description:
      - Destination folder, absolute or relative path to find an existing guest or create the new guest.
      - The folder should include the datacenter. ESX's datacenter is ha-datacenter
    required: false
  vnc_ip:
    description:
      - Sets an IP for VNC on virtual machine.
      - This is required only when I(state) is set to present and will be ignored if I(state) is absent.
    default: 0.0.0.0
    required: false
  vnc_port:
    description:
      - The port that VNC listens on. Usually a number between 5900 and 7000 depending on your config.
      - This is required only when I(state) is set to present and will be ignored if I(state) is absent.
    default: 0
    required: false
  vnc_password:
    description:
      - Sets a password for VNC on virtual machine.
      - This is required only when I(state) is set to present and will be ignored if I(state) is absent.
    default: ""
    required: false

extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: enable VNC remote display on the VM
  vmware_guest_vnc:
    hostname: 192.168.1.1
    username: administrator@vsphere.local
    password: secret321
    validate_certs: no
    folder: /mydatacenter/vm
    name: testvm1
    vnc_port: 5990
    vnc_password: vNc5ecr3t
    state: present
  delegate_to: localhost
  register: vnc_result

- name: disable VNC remote display on the VM
  vmware_guest_vnc:
    hostname: 192.168.1.1
    username: administrator@vsphere.local
    password: secret321
    validate_certs: no
    uuid: 32074771-7d6b-699a-66a8-2d9cf8236fff
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
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, set_vnc_extraconfig


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present', choices=['present', 'absent']),
        name=dict(type='str'),
        name_match=dict(type='str', choices=['first', 'last'], default='first'),
        uuid=dict(type='str'),
        folder=dict(type='str'),
        vnc_ip=dict(type='str', default='0.0.0.0'),
        vnc_port=dict(type='int', default=0),
        vnc_password=dict(type='str', default='', no_log=True),
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False,
                           mutually_exclusive=[['name', 'uuid']])

    result = dict(changed=False,)

    pyv = PyVmomi(module)
    vm = pyv.get_vm()
    if vm:
        result = set_vnc_extraconfig(
            pyv.content,
            vm,
            (module.params['state'] == "present"),
            module.params['vnc_ip'],
            module.params['vnc_port'],
            module.params['vnc_password'])
    else:
        module.fail_json(
            msg="Unable to set VNC config for non-existing virtual machine : '%s'" %
            (module.params.get('uuid') or module.params.get('name')))

    if result.get('failed') is True:
        module.fail_json(**result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
