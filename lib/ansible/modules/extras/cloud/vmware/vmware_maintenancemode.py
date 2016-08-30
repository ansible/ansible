#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, VMware, Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


DOCUMENTATION = '''
---
module: vmware_maintenancemode
short_description: Place a host into maintenance mode
description:
    - Place an ESXI host into maintenance mode
    - Support for VSAN compliant maintenance mode when selected
author: "Jay Jahns <jjahns@vmware.com>"
version_added: "2.1"
notes:
    - Tested on vSphere 5.5 and 6.0
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    esxi_hostname:
        description:
            - Name of the host as defined in vCenter
        required: True
    vsan_mode:
        description:
            - Specify which VSAN compliant mode to enter
        choices:
            - 'ensureObjectAccessibility'
            - 'evacuateAllData'
            - 'noAction'
        required: False
    evacuate:
        description:
            - If True, evacuate all powered off VMs
        choices:
            - True
            - False
        default: False
        required: False
    timeout:
        description:
            - Specify a timeout for the operation
        required: False
        default: 0
    state:
        description:
            - Enter or exit maintenance mode
        choices:
            - present
            - absent
        default: present
        required: False
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Enter VSAN-Compliant Maintenance Mode
  local_action:
    module: vmware_maintenancemode
    hostname: vc_host
    username: vc_user
    password: vc_pass
    esxi_hostname: esxi.host.example
    vsan: ensureObjectAccessibility
    evacuate: yes
    timeout: 3600
    state: present
'''
RETURN = '''
hostsystem:
    description: Name of vim reference
    returned: always
    type: string
    sample: "'vim.HostSystem:host-236'"
hostname:
    description: Name of host in vCenter
    returned: always
    type: string
    sample: "esxi.local.domain"
status:
    description: Action taken
    return: always
    type: string
    sample: "ENTER"
'''

try:
    from pyVmomi import vim
    HAS_PYVMOMI = True

except ImportError:
    HAS_PYVMOMI = False


def EnterMaintenanceMode(module, host):

    if host.runtime.inMaintenanceMode:
        module.exit_json(
            changed=False,
            hostsystem=str(host),
            hostname=module.params['esxi_hostname'],
            status='NO_ACTION',
            msg='Host already in maintenance mode')

    spec = vim.host.MaintenanceSpec()

    if module.params['vsan']:
        spec.vsanMode = vim.vsan.host.DecommissionMode()
        spec.vsanMode.objectAction = module.params['vsan']

    try:
        task = host.EnterMaintenanceMode_Task(
            module.params['timeout'],
            module.params['evacuate'],
            spec)

        success, result = wait_for_task(task)

        return dict(changed=success,
                    hostsystem=str(host),
                    hostname=module.params['esxi_hostname'],
                    status='ENTER',
                    msg='Host entered maintenance mode')

    except TaskError:
        module.fail_json(
            msg='Host failed to enter maintenance mode')


def ExitMaintenanceMode(module, host):
    if not host.runtime.inMaintenanceMode:
        module.exit_json(
            changed=False,
            hostsystem=str(host),
            hostname=module.params['esxi_hostname'],
            status='NO_ACTION',
            msg='Host not in maintenance mode')

    try:
        task = host.ExitMaintenanceMode_Task(
            module.params['timeout'])

        success, result = wait_for_task(task)

        return dict(changed=success,
                    hostsystem=str(host),
                    hostname=module.params['esxi_hostname'],
                    status='EXIT',
                    msg='Host exited maintenance mode')

    except TaskError:
        module.fail_json(
            msg='Host failed to exit maintenance mode')


def main():
    spec = vmware_argument_spec()
    spec.update(dict(
        esxi_hostname=dict(required=True),
        vsan=dict(required=False, choices=['ensureObjectAccessibility',
                                           'evacuateAllData',
                                           'noAction']),
        evacuate=dict(required=False, type='bool', default=False),
        timeout=dict(required=False, default=0, type='int'),
        state=dict(required=False,
                   default='present',
                   choices=['present', 'absent'])))

    module = AnsibleModule(argument_spec=spec)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    content = connect_to_api(module)
    host = find_hostsystem_by_name(content, module.params['esxi_hostname'])

    if not host:
        module.fail_json(
            msg='Host not found in vCenter')

    if module.params['state'] == 'present':
        result = EnterMaintenanceMode(module, host)

    elif module.params['state'] == 'absent':
        result = ExitMaintenanceMode(module, host)

    module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.vmware import *


if __name__ == '__main__':
    main()
