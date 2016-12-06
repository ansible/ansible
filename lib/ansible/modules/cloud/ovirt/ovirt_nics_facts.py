#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
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
#

import fnmatch
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    check_sdk,
    create_connection,
    get_dict_of_struct,
    ovirt_full_argument_spec,
    search_by_name,
)


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: ovirt_nics_facts
short_description: Retrieve facts about one or more oVirt virtual machine network interfaces
author: "Ondra Machacek (@machacekondra)"
version_added: "2.3"
description:
    - "Retrieve facts about one or more oVirt virtual machine network interfaces."
notes:
    - "This module creates a new top-level C(ovirt_nics) fact, which
       contains a list of NICs."
options:
    vm:
        description:
            - "Name of the VM where NIC is attached."
        required: true
    name:
        description:
            - "Name of the NIC, can be used as glob expression."
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Gather facts about all NICs which names start with C(eth) for VM named C(centos7):
- ovirt_nics_facts:
    vm: centos7
    name: eth*
- debug:
    var: ovirt_nics
'''

RETURN = '''
ovirt_nics:
    description: "List of dictionaries describing the network interfaces. NIC attribues are mapped to dictionary keys,
                  all NICs attributes can be found at following url: https://ovirt.example.com/ovirt-engine/api/model#types/nic."
    returned: On success.
    type: list
'''


def main():
    argument_spec = ovirt_full_argument_spec(
        vm=dict(required=True),
        name=dict(default=None),
    )
    module = AnsibleModule(argument_spec)
    check_sdk(module)

    try:
        connection = create_connection(module.params.pop('auth'))
        vms_service = connection.system_service().vms_service()
        vm_name = module.params['vm']
        vm = search_by_name(vms_service, vm_name)
        if vm is None:
            raise Exception("VM '%s' was not found." % vm_name)

        nics_service = vms_service.service(vm.id).nics_service()
        if module.params['name']:
            nics = [
                e for e in nics_service.list()
                if fnmatch.fnmatch(e.name, module.params['name'])
            ]
        else:
            nics = nics_service.list()

        module.exit_json(
            changed=False,
            ansible_facts=dict(
                ovirt_nics=[
                    get_dict_of_struct(c) for c in nics
                ],
            ),
        )
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=False)


if __name__ == '__main__':
    main()
