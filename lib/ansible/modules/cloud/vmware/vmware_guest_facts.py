#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This module is also sponsored by E.T.A.I. (www.etai.fr)
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vmware_guest_facts
short_description: Gather facts about a single VM
description:
    - Gather facts about a single VM on a VMware ESX cluster
version_added: 2.3
author:
    - Loic Blot (@nerzhul) <loic.blot@unix-experience.fr>
notes:
    - Tested on vSphere 5.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
   name:
        description:
            - Name of the VM to work with
        required: True
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
            - Destination folder, absolute path to find an existing guest.
            - This is required if name is supplied.
   datacenter:
        description:
            - Destination datacenter for the deploy operation
        required: True
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Gather VM facts
  vmware_guest_facts:
    hostname: 192.168.1.209
    username: administrator@vsphere.local
    password: vmware
    validate_certs: no
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
  delegate_to: localhost
  register: facts
'''

RETURN = """
instance:
    description: metadata about the virtual machine
    returned: always
    type: dict
    sample: None
"""

import os

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.vmware import PyVmomiHelper


def main():
    module = AnsibleModule(
        argument_spec=dict(
            hostname=dict(
                type='str',
                default=os.environ.get('VMWARE_HOST')
            ),
            username=dict(
                type='str',
                default=os.environ.get('VMWARE_USER')
            ),
            password=dict(
                type='str', no_log=True,
                default=os.environ.get('VMWARE_PASSWORD')
            ),
            validate_certs=dict(required=False, type='bool', default=True),
            name=dict(required=True, type='str'),
            name_match=dict(required=False, type='str', default='first'),
            uuid=dict(required=False, type='str'),
            folder=dict(required=False, type='str', default='/vm'),
            datacenter=dict(required=True, type='str'),
        ),
    )

    pyv = PyVmomiHelper(module)

    # Build searchpath for FindByInventoryPath
    searchpath = PyVmomiHelper.construct_vm_searchpath(
        module.params['datacenter'],
        module.params['folder']
    )

    # Check if the VM exists before continuing
    vm = pyv.getvm(name=module.params['name'],
                   searchpath=searchpath,
                   uuid=module.params['uuid'])

    # VM already exists
    if vm:
        try:
            module.exit_json(instance=pyv.gather_facts(vm))
        except Exception:
            e = get_exception()
            module.fail_json(msg="Fact gather failed with exception %s" % e)
    else:
        msg = "Unable to gather facts for non-existing VM"
        msg += " %s in folder %s" % (module.params['name'], searchpath)
        module.fail_json(msg=msg)

if __name__ == '__main__':
    main()
