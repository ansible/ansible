#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Joseph Callen <jcallen () csc.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vmware_target_canonical_facts
short_description: Return canonical (NAA) from an ESXi host
description:
    - Return canonical (NAA) from an ESXi host based on SCSI target ID
version_added: "2.0"
author: Joseph Callen
notes:
requirements:
    - Tested on vSphere 5.5
    - PyVmomi installed
options:
    target_id:
        description:
            - The target id based on order of scsi device
        required: True
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
# Example vmware_target_canonical_facts command from Ansible Playbooks
- name: Get Canonical name
  local_action:
    module: vmware_target_canonical_facts
    hostname: "{{ ansible_ssh_host }}"
    username: root
    password: vmware
    target_id: 7
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import HAS_PYVMOMI, connect_to_api, get_all_objs, vmware_argument_spec


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


if __name__ == '__main__':
    main()
