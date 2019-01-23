#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, Mike Klebolt  <michael.klebolt@centurylink.com>
# Copyright: (c) 2018, Andrew J. Huffman <ahuffman@redhat.com>
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
module: vmware_guest_tools
short_description: Module to manage the upgrade/mount/unmount installation of VMWare Tools
version_added: 2.8
description:
    - This module upgrades the VMWare Tools on Windows and Linux guests with state: "upgrade".
    - This module mounts the VMWare Tools installer ISO with state: "mount".
    - This module unmounts the VMWare Tools installer ISO with state: "unmount". 
requirements:
    - "python >= 2.6"
    - PyVmomi
notes:
    - In order to upgrade/mount/unmount VMWare Tools, please power on virtual machine before hand - either 'manually' or using module M(vmware_guest_powerstate).
options:
   name:
        description:
            - Name of the virtual machine to work with.
            - This is required if C(UUID) is not supplied.
   name_match:
        description:
            - If multiple virtual machines matching the name, use the first or last found.
        default: 'first'
        choices: ['first', 'last']
   uuid:
        description:
            - UUID of the instance to manage if known, this is VMware's unique identifier.
            - This is required if C(name) is not supplied.
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
            - '   folder: vm/folder2'
   datacenter:
        description:
            - Destination datacenter where the virtual machine exists.
        required: True
   state:
        description:
            - One of the following states:
            - upgrade - upgrades the VMWare Tools on Windows and Linux guests.
            - '  VMWare Tools must already be installed to upgrade.'
            - mount - mounts the VMWare Tools ISO on Windows and Linux guests.
            - unmount - unmounts the VMWare Tools ISO on Windows and Linux guests.
        choices: ['mount','unmount','upgrade']
extends_documentation_fragment: vmware.documentation
author:
    - Mike Klebolt (@MikeKlebolt) <michael.klebolt@centurylink.com>
    - Andrew J. Huffman <ahuffman@redhat.com>
'''

EXAMPLES = '''
- name: "Upgrade VMWare Tools"
  vmware_guest_tools:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    uuid: "421e4592-c069-924d-ce20-7e7533fab926"
    state: "upgrade"
  delegate_to: "localhost"

- name: "Mount VMWare Tools"
  vmware_guest_tools:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    folder: "{{ vm_folder }}"
    name: "{{ new_vm_name }}"
    validate_certs: no
    state: "mount"
  delegate_to: "localhost"

- name: "Unmount VMWare Tools"
  vmware_guest_tools:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    folder: "{{ vm_folder }}"
    name: "{{ new_vm_name }}"
    validate_certs: no
    state: "unmount"
  delegate_to: "localhost"
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
                msg="VMWare tools could not be upgraded",
            )
            return result

    def mount_tools(self, vm):
        result = {'failed': False, 'changed': False, 'msg': ''}
        # fail if VM is not powered on
        if vm.summary.runtime.powerState != "poweredOn":
            result['failed'] = True
            result['msg'] = "VM must be powered on to unmount tools"
            return result
        # mount tools
        else:
            try:
                # Tools not mounted
                if not vm.summary.runtime.toolsInstallerMounted:
                    task = vm.MountToolsInstaller()
                    changed, err_msg = wait_for_task(task)
                    result['changed'] = True
                    result['failed'] = False
                    result['msg'] = 'VMWare Tools installer has been mounted.'
                # Tools already mounted
                elif vm.summary.runtime.toolsInstallerMounted:
                    result['changed'] = False
                    result['failed'] = False
                    result['msg'] = 'VMWare Tools installer is already mounted.'
                # Everything else
                else:
                    result['changed'] = False
                    result['failed'] = True
                    result['msg'] = 'Unknown Error while mounting VMware tools.'
                return result
            except Exception as exc:
                # Already mounted (not changed)
                if 'vim.fault.InvalidState' in to_native(exc):
                    result['changed'] = False
                    result['msg'] = 'VMWare Tools installer is already mounted.'
                    result['failed'] = False
                # Successful mount (changed)
                elif 'NoneType' in to_native(exc):
                    result['changed'] = True
                    result['msg'] = 'VMWare Tools installer has been mounted.'
                    result['failed'] = False
                else:
                    result['changed'] = False
                    result['failed'] = True
                    result['msg'] = 'Error while mounting VMware tools %s' % to_native(exc)
                return result

    def unmount_tools(self, vm):
        result = {'failed': False, 'changed': False, 'msg': ''}
        # fail if VM is not powered on
        if vm.summary.runtime.powerState != "poweredOn":
            result['failed'] = True
            result['msg'] = "VM must be powered on to unmount tools"
            return result
        # unmount tools
        else:
            try:
                # Tools already mounted
                if vm.summary.runtime.toolsInstallerMounted:
                    task = vm.UnmountToolsInstaller()
                    changed, err_msg = wait_for_task(task)
                    result['changed'] = True
                    result['msg'] = 'VMWare Tools installer has been unmounted.'
                    result['failed'] = False
                # Tools not mounted
                elif not vm.summary.runtime.toolsInstallerMounted:
                    result['changed'] = False
                    result['msg'] = 'VMWare Tools installer is already unmounted.'
                    result['failed'] = False
                # Everything else
                else:
                    result['failed'] = True
                    result['changed'] = False
                    result['msg'] = 'Unknown Error while unmounting VMware tools.'
                return result
            except Exception as exc:
                # already unmounted (not changed)
                if 'vim.fault.InvalidState' in to_native(exc):
                    result['changed'] = False
                    result['msg'] = 'VMWare Tools installer is already unmounted.'
                    result['failed'] = False
                # successful unmount (changed)
                elif 'NoneType' in to_native(exc):
                    result['changed'] = True
                    result['msg'] = 'VMWare Tools installer has been unmounted.'
                    result['failed'] = False
                else:
                    result['changed'] = False
                    result['failed'] = True
                    result['msg'] = 'Error while unmounting VMware tools %s' % to_native(exc)
                return result
def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        name_match=dict(type='str', choices=['first', 'last'], default='first'),
        uuid=dict(type='str'),
        folder=dict(type='str'),
        datacenter=dict(type='str', required=True),
        state=dict(type='str', choices=['mount', 'unmount', 'upgrade'], required=True),
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=[['name', 'uuid']])

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
            if module.params['state'] == 'upgrade':
                result = pyv.upgrade_tools(vm)
            elif module.params['state'] == 'mount':
                result = pyv.mount_tools(vm)
            elif module.params['state'] == 'unmount':
                result = pyv.unmount_tools(vm)
            else:
                result.update(
                    failed=True,
                    msg="You must provide a valid state: 'mount', 'unmount', 'upgrade'."
                )
                return result
            if result['changed']:
                module.exit_json(changed=result['changed'])
            elif result['failed']:
                module.fail_json(msg=result['msg'])
            else:
                module.exit_json(msg=result['msg'], changed=result['changed'])
        except Exception as exc:
            module.fail_json(msg='Unknown error: %s' % to_native(exc))
    else:
        module.fail_json(msg='Unable to find VM %s' % (module.params.get('uuid') or module.params.get('name')))


if __name__ == '__main__':
    main()
