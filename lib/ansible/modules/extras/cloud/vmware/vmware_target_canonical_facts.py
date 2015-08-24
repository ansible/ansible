#!/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Joseph Callen <jcallen () csc.com>
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
module: vmware_target_canonical_facts
short_description: Return canonical (NAA) from an ESXi host
description:
    - Return canonical (NAA) from an ESXi host based on SCSI target ID
version_added: 2.0
author: Joseph Callen
notes:
requirements:
    - Tested on vSphere 5.5
    - PyVmomi installed
options:
 hostname:
        description:
            - The hostname or IP address of the vSphere vCenter
        required: True
    username:
        description:
            - The username of the vSphere vCenter
        required: True
        aliases: ['user', 'admin']
    password:
        description:
            - The password of the vSphere vCenter
        required: True
        aliases: ['pass', 'pwd']
    target_id:
        description:
            - The target id based on order of scsi device
        required: True
'''

EXAMPLES = '''
# Example vmware_target_canonical_facts command from Ansible Playbooks
- name: Get Canonical name
      local_action: >
        vmware_target_canonical_facts
        hostname="{{ ansible_ssh_host }}" username=root password=vmware
        target_id=7
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


def find_hostsystem(content):
    host_system = get_all_objs(content, [vim.HostSystem])
    for host in host_system:
        return host
    return None


def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(target_id=dict(required=True, type='int')))
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    content = connect_to_api(module)
    host = find_hostsystem(content)

    target_lun_uuid = {}
    scsilun_canonical = {}

    # Associate the scsiLun key with the canonicalName (NAA)
    for scsilun in host.config.storageDevice.scsiLun:
        scsilun_canonical[scsilun.key] = scsilun.canonicalName

    # Associate target number with LUN uuid
    for target in host.config.storageDevice.scsiTopology.adapter[0].target:
        for lun in target.lun:
            target_lun_uuid[target.target] = lun.scsiLun

    module.exit_json(changed=False, canonical=scsilun_canonical[target_lun_uuid[module.params['target_id']]])

from ansible.module_utils.basic import *
from ansible.module_utils.vmware import *

if __name__ == '__main__':
    main()

