#!/usr/bin/python
# -*- coding: utf-8 -*-

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
version_added: "2.7"
description:
    - "This module upgrades the VMWare Tools on Windows and Linux guests."
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
   name:
        description:
            - Name of the VM to work with
            - This is required if UUID is not supplied.
   name_match:
        description:
            - If multiple VMs matching the name, use the first or last found
        default: 'first'
        choices: ['first', 'last']
   uuid:
        description:
            - UUID of the instance to manage if known, this is VMware's unique identifier.
            - This is required if name is not supplied.
   folder:
        description:
            - Destination folder, absolute or relative path to find an existing guest.
            - This is required if name is supplied.
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
            - '   folder: folder2'
        default: /vm
   datacenter:
        description:
            - Destination datacenter for the deploy operation
        required: True
extends_documentation_fragment: vmware.documentation
author:
    - Mike Klebolt (@MikeKlebolt) <michael.klebolt@centurylink.com>
'''

EXAMPLES = '''
- name: Upgrade VMWare Tools
  vmware_guest_facts:
    hostname: 192.168.1.209
    username: administrator@vsphere.local
    password: vmware
    datacenter: ha-datacenter
    validate_certs: no
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
  delegate_to: localhost
'''

RETURN = ''' # '''

try:
    import pyVmomi
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import (PyVmomi, gather_vm_facts, vmware_argument_spec,
                                         wait_for_task)


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
                wait_for_task(task)
                result.update(
                    changed=True,
                )
                return result
            except Exception as exc:
                result.update(
                    failed=True,
                    msg='Error while upgrading VMware tools %s' % exc,
                )
                return result
        else:
            result.update(
                failed=True,
                msg="VMWare tools could not be upgraded",
            )
            return result


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        name_match=dict(type='str', choices=['first', 'last'], default='first'),
        uuid=dict(type='str'),
        folder=dict(type='str', default='/vm'),
        datacenter=dict(type='str', required=True),
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
            result = pyv.upgrade_tools(vm)
            if result['changed']:
                module.exit_json(changed=result['changed'])
            elif result['failed']:
                module.fail_json(msg=result['msg'])
            else:
                module.exit_json(msg=result['msg'], changed=result['changed'])
        except Exception as exc:
            module.fail_json(msg='Unknown error: %s' % exc)


if __name__ == '__main__':
    main()
