#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, Mike Klebolt  <michael.klebolt@centurylink.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: vmware_guest_tools_upgrade
short_description: Module to upgrade VMTools
version_added: 2.8
description:
    - This module upgrades the VMware Tools on Windows and Linux guests.
requirements:
    - "python >= 2.6"
    - PyVmomi
notes:
    - In order to upgrade VMTools, please power on virtual machine before hand - either 'manually' or using module M(vmware_guest_powerstate).
options:
   name:
        description:
            - Name of the virtual machine to work with.
            - This is required if C(uuid) or C(moid) is not supplied.
        type: str
   name_match:
        description:
            - If multiple virtual machines matching the name, use the first or last found.
        default: 'first'
        choices: ['first', 'last']
        type: str
   uuid:
        description:
            - UUID of the instance to manage if known, this is VMware's unique identifier.
            - This is required if C(name) or C(moid) is not supplied.
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
            - This is required, if C(name) is supplied.
            - The folder should include the datacenter. ESX's datacenter is ha-datacenter
            - 'Examples:'
            - '   folder: /ha-datacenter/vm'
            - '   folder: ha-datacenter/vm'
            - '   folder: /datacenter1/vm'
            - '   folder: datacenter1/vm'
            - '   folder: /datacenter1/vm/folder1'
            - '   folder: datacenter1/vm/folder1'
            - '   folder: /folder1/datacenter1/vm'
            - '   folder: folder1/datacenter1/vm'
            - '   folder: /folder1/datacenter1/vm/folder2'
        type: str
   datacenter:
        description:
            - Destination datacenter where the virtual machine exists.
        required: True
        type: str
extends_documentation_fragment: vmware.documentation
author:
    - Mike Klebolt (@MikeKlebolt) <michael.klebolt@centurylink.com>
'''

EXAMPLES = '''
- name: Upgrade VMware Tools using uuid
  vmware_guest_tools_upgrade:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
  delegate_to: localhost

- name: Upgrade VMware Tools using MoID
  vmware_guest_tools_upgrade:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    moid: vm-42
  delegate_to: localhost
'''

RETURN = ''' # '''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, wait_for_task
from ansible.module_utils._text import to_native


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)

    def upgrade_tools(self, vm):
        result = {'failed': False, 'changed': False, 'msg': ''}
        # Exit if VMware tools is already up to date
        if vm.guest.toolsStatus == "toolsOk":
            result.update(
                changed=False,
                msg="VMware tools is already up to date",
            )
            return result

        # Fail if VM is not powered on
        elif vm.summary.runtime.powerState != "poweredOn":
            result.update(
                failed=True,
                msg="VM must be powered on to upgrade tools",
            )
            return result

        # Fail if VMware tools is either not running or not installed
        elif vm.guest.toolsStatus in ["toolsNotRunning", "toolsNotInstalled"]:
            result.update(
                failed=True,
                msg="VMware tools is either not running or not installed",
            )
            return result

        # If vmware tools is out of date, check major OS family
        # Upgrade tools on Linux and Windows guests
        elif vm.guest.toolsStatus == "toolsOld":
            try:
                if vm.guest.guestFamily in ["linuxGuest", "windowsGuest"]:
                    task = vm.UpgradeTools()
                    changed, err_msg = wait_for_task(task)
                    result.update(changed=changed, msg=to_native(err_msg))
                else:
                    result.update(msg='Guest Operating System is other than Linux and Windows.')
                return result
            except Exception as exc:
                result.update(
                    failed=True,
                    msg='Error while upgrading VMware tools %s' % to_native(exc),
                )
                return result
        else:
            result.update(
                failed=True,
                msg="VMware tools could not be upgraded",
            )
            return result


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        name_match=dict(type='str', choices=['first', 'last'], default='first'),
        uuid=dict(type='str'),
        moid=dict(type='str'),
        folder=dict(type='str'),
        datacenter=dict(type='str', required=True),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['name', 'uuid', 'moid']
        ]
    )

    if module.params['folder']:
        # FindByInventoryPath() does not require an absolute path
        # so we should leave the input folder path unmodified
        module.params['folder'] = module.params['folder'].rstrip('/')

    pyv = PyVmomiHelper(module)
    # Check if the VM exists before continuing
    vm = pyv.get_vm()

    # VM already exists
    if vm:
        try:
            result = pyv.upgrade_tools(vm)
            if result['changed']:
                module.exit_json(changed=result['changed'])
            elif result['failed']:
                module.fail_json(msg=result['msg'])
            else:
                module.exit_json(msg=result['msg'], changed=result['changed'])
        except Exception as exc:
            module.fail_json(msg='Unknown error: %s' % to_native(exc))
    else:
        vm_id = module.params.get('uuid') or module.params.get('name') or module.params.get('moid')
        module.fail_json(msg='Unable to find VM %s' % vm_id)


if __name__ == '__main__':
    main()
