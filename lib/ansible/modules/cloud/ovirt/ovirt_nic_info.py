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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt_nic_info
short_description: Retrieve information about one or more oVirt/RHV virtual machine network interfaces
author: "Ondra Machacek (@machacekondra)"
version_added: "2.3"
description:
    - "Retrieve information about one or more oVirt/RHV virtual machine network interfaces."
    - This module was called C(ovirt_nic_facts) before Ansible 2.9, returning C(ansible_facts).
      Note that the M(ovirt_nic_info) module no longer returns C(ansible_facts)!
notes:
    - "This module returns a variable C(ovirt_nics), which
       contains a list of NICs. You need to register the result with
       the I(register) keyword to use it."
options:
    vm:
        description:
            - "Name of the VM where NIC is attached."
        required: true
    name:
        description:
            - "Name of the NIC, can be used as glob expression."
extends_documentation_fragment: ovirt_info
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Gather information about all NICs which names start with C(eth) for VM named C(centos7):
- ovirt_nic_info:
    vm: centos7
    name: eth*
  register: result
- debug:
    msg: "{{ result.ovirt_nics }}"
'''

RETURN = '''
ovirt_nics:
    description: "List of dictionaries describing the network interfaces. NIC attributes are mapped to dictionary keys,
                  all NICs attributes can be found at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/nic."
    returned: On success.
    type: list
'''

import fnmatch
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    check_sdk,
    create_connection,
    get_dict_of_struct,
    ovirt_info_full_argument_spec,
    search_by_name,
)


def main():
    argument_spec = ovirt_info_full_argument_spec(
        vm=dict(required=True),
        name=dict(default=None),
    )
    module = AnsibleModule(argument_spec)
    is_old_facts = module._name == 'ovirt_nic_facts'
    if is_old_facts:
        module.deprecate("The 'ovirt_nic_facts' module has been renamed to 'ovirt_nic_info', "
                         "and the renamed one no longer returns ansible_facts", version='2.13')

    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
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

        result = dict(
            ovirt_nics=[
                get_dict_of_struct(
                    struct=c,
                    connection=connection,
                    fetch_nested=module.params.get('fetch_nested'),
                    attributes=module.params.get('nested_attributes'),
                ) for c in nics
            ],
        )
        if is_old_facts:
            module.exit_json(changed=False, ansible_facts=result)
        else:
            module.exit_json(changed=False, **result)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == '__main__':
    main()
